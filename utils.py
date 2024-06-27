def update_search_history(search_term):
    search_history_file = 'search_history.txt'
    max_history_size = 5
    
    try:
        with open(search_history_file, 'r') as file:
            search_history = file.read().splitlines()
    except FileNotFoundError:
        search_history = []
    
    if search_term in search_history:
        search_history.remove(search_term)
    search_history.insert(0, search_term)
    search_history = search_history[:max_history_size]
    
    with open(search_history_file, 'w') as file:
        for term in search_history:
            file.write(term + '\n')

def get_search_history():
    search_history_file = 'search_history.txt'
    
    try:
        with open(search_history_file, 'r') as file:
            search_history = file.read().splitlines()
    except FileNotFoundError:
        search_history = []
    
    return search_history
