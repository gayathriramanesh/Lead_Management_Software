from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def lead(request):
     data=request.parse(request.body)
     insert_into_db(data)
     return HttpResponse("Lead created successfully", status=201)

def insert_into_db(data):
     name=data.get("name")
     if not name:
            return HttpResponse("Name is required", status=400)
     age=data.get("age")
     if not age:
            return HttpResponse("Age is required", status=400)
     email=data.get("email")
     if not email:
            return HttpResponse("Email is required", status=400)
     place=data.get("place")
     if not place:
            return HttpResponse("Place is required", status=400)
     status=data.get("status")
     if not status:
            return HttpResponse("Status is required", status=400)
     image_url=data.get("image_url")
     if not image_url:
            return HttpResponse("Image URL is required", status=400)
     remarks=data.get("remarks")
     if not remarks:
            return HttpResponse("Remarks is required", status=400)
     db.query("INSERT INTO lead(name, age, email, place, status, image_url, remarks) VALUES (name, age, email, place, status, image_url, remarks)")
     db.commit()
     db.close()