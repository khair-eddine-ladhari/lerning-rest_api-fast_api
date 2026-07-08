


from wsgiref import headers

import requests

"""
print(response)
print(response.status_code)

print(response.json())
print(response.text)
print(response.headers["content-type"])


data=response.json()
print(data["title"])
"""
"""
params={"userId":2}
request=requests.get("https://jsonplaceholder.typicode.com/posts",params=params)
print(request.url)
print(request.json())
print(len(request.json()))

new_post={"userId":2,"title":"My new post","body":"This is my new post"}
response=requests.post("https://jsonplaceholder.typicode.com/posts",json=new_post)
print(response.status_code)
print(response.json())
"""


"""def save_get(url):

    try:
        response=requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print("HTTP error occurred:", err)
    except requests.exceptions.RequestException as err:
        print("Request error occurred:", err)


res=save_get("https://jsonplaceholder.typicode.com/posts/1")
print(res)
  """
"""response = requests.post(
    "https://dummyjson.com/auth/login",
    json={"username": "emilys", "password": "emilyspass"}
)


token=response.json()["accessToken"]
authentication={"Authorization": f"Bearer {token}"}
me_response = requests.get("https://dummyjson.com/auth/me")
print(me_response.status_code)
print(me_response.json())

"""

"""
req1=requests.get("https://jsonplaceholder.typicode.com/posts/1")
print(req1.headers["content-type"])
req2=requests.get("https://jsonplaceholder.typicode.com/posts/1",headers={"Accept":"application/xml"})
print(req2.headers["content-type"])"""




def create_todo(title,userId):

    try:


        new_todo={"userId":userId,"title":title,"completed":False}   
        response=requests.post("https://jsonplaceholder.typicode.com/todos", json=new_todo)
        response.raise_for_status()
        print(response.status_code)
    
        return response.json()
    except requests.exceptions.HTTPError as err:
        print("HTTP error occurred:", err)
    except requests.exceptions.RequestException as err:
        print("Request error occurred:", err)


def get_todos(userId):
    try:

        response=requests.get(f"https://jsonplaceholder.typicode.com/todos?userId={userId}")
        response.raise_for_status()
        print(response.status_code)
        return response.json()
    except requests.exceptions.HTTPError as err:
        print("HTTP error occurred:", err)
    except requests.exceptions.RequestException as err:
        print("Request error occurred:", err)
    




def main():
    
    print("Creating a new todo...")
    id_user=int(input("Enter userId: "))

    todos=get_todos(id_user)
    if todos is None:
        print("Failed to retrieve todos.")
        return
    for todo in todos:
        print(f"Todo ID: {todo['id']}, Title: {todo['title']}, Completed: {todo['completed']}")
    print("Creating a new todo...")
    title=input("Enter title for the new todo: ")

    new_todo=create_todo(title,id_user)
    print(f"New todo created: {new_todo}")



main()