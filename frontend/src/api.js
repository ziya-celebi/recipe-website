                                                                                                                                                                       
const API_BASE = import.meta.env.DEV ? 'http://localhost:8000' : ''                                                                                                
                                                                                                                                                                       
export async function fetchRecipes(query = '') {                                                                                                                       
  const url = query                                                                                                                                                    
    ? `${API_BASE}/api/recipes?q=${encodeURIComponent(query)}`                                                                                                             
    : `${API_BASE}/api/recipes`                                                                                                                                            
  const res = await fetch(url)                                                                                                                                         
  if (!res.ok) throw new Error('Network response was not ok')                                                                                                          
  return res.json()                                                                                                                                                    
}                                                                                                                                                                      
                                                                                                                                                                       
export async function fetchRecipe(id) {                                                                                                                                
  const res = await fetch(`${API_BASE}/api/recipes/${id}`)                                                                                                                 
  if (res.status === 404) throw new Error('Recipe not found')                                                                                                          
  if (!res.ok) throw new Error('Network response was not ok')                                                                                                          
  return res.json()                                                                                                                                                    
}   