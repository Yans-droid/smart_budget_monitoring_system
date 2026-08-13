import api from './api'

export const classificationApi = {
  /**
   * Classify a single text
   * @param {string} text
   */
  classifySingle(text) {
    return api.post('/classification/classify', { text })
      .then(res => res.data)
  },

  /**
   * Classify multiple texts (without saving to DB)
   * @param {string[]} items - array of text strings
   */
  classifyBulk(items) {
    return api.post('/classification/classify/bulk', { items })
      .then(res => res.data)
  },

  /**
   * Classify a single PrPoData record and save result
   * @param {number} prPoDataId
   */
  classifyPrPo(prPoDataId) {
    return api.post(`/classification/classify/pr-po/${prPoDataId}`)
      .then(res => res.data)
  },

  /**
   * Classify all WAITING records from an upload batch
   * @param {number} uploadId
   */
  classifyByUpload(uploadId) {
    return api.post(`/classification/classify/upload/${uploadId}`)
      .then(res => res.data)
  },
}
