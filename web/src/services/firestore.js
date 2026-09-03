/**
 * Firestore REST API Client for Upshift Web Control Hub
 * Enables instant zero-dependency reads/writes to Firestore collections.
 */

const PROJECT_ID = "upshiftjobs";
const API_KEY = "AIzaSyC2gQprgxVB_zEY_MLWaY08mC9__w2pySQ";
const BASE_URL = `https://firestore.googleapis.com/v1/projects/${PROJECT_ID}/databases/(default)/documents`;

/**
 * Converts a plain JS object into Firestore typed fields.
 */
function toFirestoreFields(obj) {
  const fields = {};
  for (const [key, value] of Object.entries(obj)) {
    if (value === null || value === undefined) {
      fields[key] = { nullValue: null };
    } else if (typeof value === "boolean") {
      fields[key] = { booleanValue: value };
    } else if (typeof value === "number") {
      if (Number.isInteger(value)) {
        fields[key] = { integerValue: value.toString() };
      } else {
        fields[key] = { doubleValue: value };
      }
    } else if (Array.isArray(value)) {
      fields[key] = {
        arrayValue: {
          values: value.map((item) => {
            if (typeof item === "string") return { stringValue: item };
            if (typeof item === "number") return { integerValue: item.toString() };
            return { stringValue: String(item) };
          })
        }
      };
    } else if (typeof value === "object") {
      fields[key] = { mapValue: { fields: toFirestoreFields(value) } };
    } else {
      fields[key] = { stringValue: String(value) };
    }
  }
  return fields;
}

/**
 * Converts Firestore typed fields into a clean JS object.
 */
function fromFirestoreFields(fields = {}) {
  const result = {};
  for (const [key, field] of Object.entries(fields)) {
    if (!field || typeof field !== "object") continue;
    if ("stringValue" in field) {
      result[key] = field.stringValue;
    } else if ("integerValue" in field) {
      result[key] = parseInt(field.integerValue, 10);
    } else if ("doubleValue" in field) {
      result[key] = parseFloat(field.doubleValue);
    } else if ("booleanValue" in field) {
      result[key] = field.booleanValue;
    } else if ("nullValue" in field) {
      result[key] = null;
    } else if ("mapValue" in field) {
      result[key] = fromFirestoreFields(field.mapValue.fields || {});
    } else if ("arrayValue" in field) {
      const rawArr = field.arrayValue.values || [];
      result[key] = rawArr.map((item) => {
        if ("stringValue" in item) return item.stringValue;
        if ("integerValue" in item) return parseInt(item.integerValue, 10);
        if ("doubleValue" in item) return parseFloat(item.doubleValue);
        if ("booleanValue" in item) return item.booleanValue;
        return item;
      });
    }
  }
  return result;
}

export const FirestoreService = {
  /**
   * Pings Firestore to verify connection and estimate latency.
   */
  async ping() {
    const start = performance.now();
    try {
      const res = await fetch(`${BASE_URL}/counters/post_counter?key=${API_KEY}`, {
        method: "GET"
      });
      const duration = Math.round(performance.now() - start);
      return { ok: res.ok, latencyMs: duration, status: res.status };
    } catch (err) {
      return { ok: false, error: err.message, latencyMs: null };
    }
  },

  /**
   * Fetches the current post counter from Firestore.
   */
  async getPostCounter() {
    const res = await fetch(`${BASE_URL}/counters/post_counter?key=${API_KEY}`);
    if (res.status === 404) {
      // Document does not exist yet; default
      return {
        global_counter: 1,
        categories: { engineering: 1, data: 1, devops: 1, product: 1 },
        last_updated_at: null,
        last_post_id: null
      };
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error?.message || `Failed to fetch counter (${res.status})`);
    }
    const data = await res.json();
    const parsed = fromFirestoreFields(data.fields || {});
    return {
      global_counter: parsed.global_counter || 1,
      categories: parsed.categories || { engineering: 1, data: 1, devops: 1, product: 1 },
      last_updated_at: parsed.last_updated_at || null,
      last_post_id: parsed.last_post_id || null
    };
  },

  /**
   * Updates the post counter document in Firestore.
   */
  async updatePostCounter(globalCounter, categories = null) {
    const payload = {
      global_counter: parseInt(globalCounter, 10),
      last_updated_at: new Date().toISOString(),
      last_post_id: `UP-${String(Math.max(1, globalCounter - 1)).padStart(4, "0")}`
    };
    if (categories) {
      payload.categories = categories;
    }

    const res = await fetch(`${BASE_URL}/counters/post_counter?key=${API_KEY}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fields: toFirestoreFields(payload) })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error?.message || `Failed to update counter (${res.status})`);
    }

    const data = await res.json();
    return fromFirestoreFields(data.fields || {});
  },

  /**
   * Resets the post counter to a given base number (default: 1).
   */
  async resetPostCounter(startFrom = 1) {
    const resetCategories = { engineering: 1, data: 1, devops: 1, product: 1 };
    return this.updatePostCounter(startFrom, resetCategories);
  },

  /**
   * Fetches published batches from the `batches` collection.
   */
  async getBatches(pageSize = 30) {
    const url = `${BASE_URL}/batches?key=${API_KEY}&pageSize=${pageSize}`;
    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error?.message || `Failed to load batches (${res.status})`);
    }
    const data = await res.json();
    const rawDocs = data.documents || [];
    const batches = rawDocs.map((doc) => {
      const parsed = fromFirestoreFields(doc.fields || {});
      const id = doc.name.split("/").pop();
      return { id, ...parsed };
    });

    // Sort descending by created_at or batch_id
    batches.sort((a, b) => (b.created_at || "").localeCompare(a.created_at || ""));
    return batches;
  },

  /**
   * Fetches full job details for a list of job IDs.
   */
  async getBatchJobs(jobIds = []) {
    if (!jobIds.length) return [];
    const promises = jobIds.map(async (jobId) => {
      try {
        const res = await fetch(`${BASE_URL}/jobs/${jobId}?key=${API_KEY}`);
        if (!res.ok) return null;
        const data = await res.json();
        return { id: jobId, ...fromFirestoreFields(data.fields || {}) };
      } catch {
        return null;
      }
    });

    const results = await Promise.all(promises);
    return results.filter(Boolean);
  }
};
