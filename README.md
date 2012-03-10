Django MongoDB ManyToManyField Implementation
=============================================

Created by Kenneth Falck <kennu@iki.fi> 2012 (http://kfalck.net)

Released under the standard BSD License (see below).

Overview
--------

This is a simple implementation of ManyToManyFields for django-mongodb-engine. The MongoDBManyToManyField
stores references to other Django model instances as ObjectIds in a MongoDB list field.

Optionally, MongoDBManyToManyField will also embed a "cached" copy of the instances inside the list. This
allows fast access to the data without having to query each related object from the database separately.

MongoDBManyToManyField attempts to work mostly in the same way as Django's built-in ManyToManyField.
Related objects can be added and removed with the add(), remove(), clear() and create() methods.

To enumerate the objects, the all() method returns a simulated QuerySet object which loads non-embedded
objects automatically from the database when needed.

On the reverse side of the relation, an accessor  property is added (usually called OtherModel.modelname\_set,
can be overridden with the related\_name attribute) to return the related objects in the reverse direction.
It uses MongoDB's raw\_query() to find all related model objects. Because of this, any data model that
uses MongoDBManyToManyField() must have a default MongoDBManager() instead of Django's normal Manager().

Usage
-----

Example model using a many-to-many field:

    from django.db import models
    from mongom2m.fields import MongoDBManyToManyField
    from django_mongodb_engine.contrib import MongoDBManager
    
    class Category(models.Model):
        objects = MongoDBManager()
        title = models.CharField(max_length=254)
    
    class Article(models.Model):
        objects = MongoDBManager()
        categories = MongoDBManyToManyField(Category)
        title = models.CharField(max_length=254)
        text = models.TextField()

To store categories in the field, you would first create the category and then add it:

    category = Category(title='foo')
    category.save()
    
    article = Article(title='bar')
    article.categories.add(category)
    article.save()
    
    for cat in article.categories.all():
        print cat.title
    
    for art in category.article_set.all():
        print art.title

License
-------

Copyright (c) 2012, Kenneth Falck
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
