const baseUrl = "https://orlovole.eu.pythonanywhere.com/api/v1";

const api = {
  location() {
    const method = "search";
    return `${baseUrl}/${method}`;
  }
};

export default api;
