# discussion-site
A STEM based discussion website similar to stack exchange. Developed in Flask.

It is only a locally hosted web app.

The database is connected through a local PostgreSQL server.

Complete with users and authentication. Posting discussions and comments and the ability to like/dislike them and a REST api to communicate with the database.

# API
This is a small documentation of the usage of the api

**Note**: the header `Content-Type` is required to be `application/json` every request
**Note**: There is currently no way to get an api key other than to manually input it into the database

**-USER-**

-- Get a specific user--
- Required parameters:
  1. id: int - ID of the user
- Usage:
   ```
   GET /127.0.0.1:5000/api/v1/user
   Content-Type: application/json
    
   {
     "id": 1
   }
   ```
- Response:
   ```
   {
    "type": "GET",
    "responseCode": 200,
    "totalResults": 1,
    "message": "success",
    "items": [
      {
        "id": 1,
        "username": "username",
        "joinedAtDate": "date",
        "joinedAtTime": "time",
        "discussions": [Discussions],
        "comments": [Comments]
      }
    ]
   }
   ```
-- Delete a user --

*Authorisation Required*

- Required parameters:
  1. id: int - ID of the user
- Usage:
   ```
   DELETE /127.0.0.1:5000/api/v1/user
   Content-Type: application/json
   Authorization: APIKEY your-key
    
   {
     "id": 1
   }
   ```
- Response:
   ```
   {
    "type": "DELETE",
    "responseCode": 200,
    "totalResults": 0,
    "message": "success",
    "items": []
   }
   ```

-- List users --

- Available parameters:
  1. maxResults: int - max results to return. Must be in range [1, 50]. Default is 5.
- Usage:
   ```
   GET /127.0.0.1:5000/api/v1/user/list
   Content-Type: application/json
    
   {
     "maxResults": 10
   }
   ```
- Response:
   ```
   {
    "type": "GET",
    "responseCode": 200,
    "totalResults": num_results,
    "message": "success",
    "items": [
     {
        "id": id,
        "username": "username",
        "joinedAtDate": "date",
        "joinedAtTime": "time",
        "discussions": [Discussions],
        "comments": [Comments]
      }
    ]
   }
   ```

This is a basic look into how the api works. 

There are requests for discussion and comments too, but they are similar.

There are also other responses for if a required parameter is not given, or you are not authorised.
