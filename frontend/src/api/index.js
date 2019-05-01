const baseUrl = "https://rickandmortyapi.com/api"

const api = {
  location() {
    const method = "location"
    return `${baseUrl}/${method}`
  }
}

export default api