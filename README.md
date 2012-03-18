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


Django compability
------------------

This implementation has been tweaked to be mostly compatible with Django admin, which means you can use
TabularInlines or filter\_horizontal and filter\_vertical to administer the many-to-many fields.

Don't be surprised, however, if some things don't work, because it's all emulated. There is no real
"through" table in the database to provide the many-to-many association.


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

To enable embedding, just add the embed=True keyword argument to the field:

    class Article(models.Model):
        categories = MongoDBManyToManyField(Category, embed=True)


Indexing
--------

Many-to-many related querying will use the "id" field the embedded model fields,
whether full embedding is used or not. If full embedding is not used, then those
fields will be sub-objects containing only an "id" field.

In either case, you should index the "id" fields properly. This can be done as follows:

    from django.db import connection
    connection.get_collection('blog_article').ensure_index([('categories.id', 1)])

(Replacing, of course, 'blog\_article' and 'categories' with the appropriate collection
and field names.)


Migrating
---------

If you have an old model that's using something like this:

    categories = ListField(EmbeddedField(Category))

You can normally change it to:

    categories = MongoDBManyToManyField(Category)

The many-to-many field's data is almost identical to that of the embedded field,
except that MongoDB object ids are stored as ObjectIds instead of strings. When
the field is loaded from the datatabase, the id strings are automatically converted
to ObjectIds. So the next time the model containing the field is saved, the ids
are written correctly.

This basically means that you may need to do a migration like this:

    for article in Article.objects.all():
        article.save()

Also make sure that the "id" field is properly indexed (see previous section).


BSD License
-----------

Copyright (c) 2012, Kenneth Falck
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
