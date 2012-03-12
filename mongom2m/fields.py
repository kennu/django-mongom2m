from djangotoolbox.fields import ListField, DictField, EmbeddedModelField, AbstractIterableField
from pymongo.objectid import ObjectId
from django.forms import ModelMultipleChoiceField
from django.db import models

class MongoDBM2MQuerySet(object):
    """
    Helper for returning a set of objects from the managers.
    Works similarly to Django's own query set objects.
    Lazily loads non-embedded objects when iterated.
    If embed=False, objects are always loaded from database.
    """
    def __init__(self, rel, objects, use_cached):
        self.rel = rel
        self.objects = list(objects) # make a copy of the list to avoid problems
        if not use_cached:
            # Reset any cached instances
            self.objects = [{'pk':obj['pk'], 'obj':None} for obj in self.objects]
    
    def __iter__(self):
        for obj in self.objects:
            if not obj['obj']:
                # Load referred instance from db and keep in memory
                obj['obj'] = self.rel.objects.get(pk=obj['pk'])
            yield obj['obj']
    
    def __getitem__(self, key):
        obj = self.objects[key]
        if not obj['obj']:
            # Load referred instance from db and keep in memory
            obj['obj'] = self.rel.objects.get(pk=obj['pk'])
        return obj['obj']
    
    def count(self):
        return len(self.objects)

class MongoDBM2MReverseManager(object):
    """
    This manager is attached to the other side of M2M relationships
    and will return query sets that fetch related objects.
    """
    def __init__(self, rel_field, model, field, rel, embed):
        self.rel_field = rel_field
        self.model = model
        self.field = field
        self.rel = rel
        self.embed = embed
    
    def all(self):
        """
        Retrieve all related objects.
        """
        name = self.field.column + '.' + self.rel._meta.pk.column
        pk = ObjectId(self.rel_field.pk)
        return self.model._default_manager.raw_query({name:pk})

class MongoDBM2MReverseDescriptor(object):
    def __init__(self, model, field, rel, embed):
        self.model = model
        self.field = field
        self.rel = rel
        self.embed = embed
    
    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return MongoDBM2MReverseManager(instance, self.model, self.field, self.rel, self.embed)

class MongoDBM2MRelatedManager(object):
    """
    This manager manages the related objects stored in a MongoDBManyToManyField.
    They can be embedded or stored as relations (ObjectIds) only.
    Internally, we store the objects as dicts that contain keys pk and obj.
    The obj key is None when the object has not yet been loaded from the db.
    """
    def __init__(self, field, rel, embed, objects=[]):
        self.field = field
        self.rel = rel
        self.embed = embed
        self.objects = list(objects) # make copy of the list to avoid problems
    
    def __call__(self):
        # This is used when creating a default value for the field
        return MongoDBM2MRelatedManager(self.field, self.rel, self.embed, self.objects)
    
    def count(self):
        return len(self.objects)
    
    def add(self, *objs):
        """
        Add model instance(s) to the M2M field. The objects can be real
        Model instances or just ObjectIds (or strings representing ObjectIds).
        """
        for obj in objs:
            if isinstance(obj, (ObjectId, basestring)):
                # It's an ObjectId
                pk = ObjectId(obj)
                instance = None
            else:
                # It's a model object
                pk = ObjectId(obj.pk)
                instance = obj
            self.objects.append({'pk':pk, 'obj':instance})
        return self
    
    def create(**kwargs):
        """
        Create new model instance and add to the M2M field.
        """
        obj = self.rel(**kwargs)
        self.add(obj)
        return obj
    
    def remove(self, *objs):
        """
        Remove the specified object from the M2M field.
        The object can be a real model instance or an ObjectId or
        a string representing an ObjectId. The related object is
        not deleted, it's only removed from the list.
        """
        obj_ids = set([ObjectId(obj) if isinstance(obj, (ObjectId, basestring)) else ObjectId(obj.pk) for obj in objs])
        self.objects = [obj for obj in self.objects if obj['pk'] not in obj_ids]
        return self
    
    def clear(self):
        """
        Clear all objecst in the list. The related objects are not
        deleted from the database.
        """
        self.objects = []
        return self
    
    def __iter__(self):
        """
        Iterator is used by Django admin's ModelMultipleChoiceField.
        """
        for obj in self.objects:
            if not obj['obj']:
                # Load referred instance from db and keep in memory
                obj['obj'] = self.rel.objects.get(pk=obj['pk'])
            yield obj['obj']
    
    def all(self):
        """
        Return all the related objects as a query set. If embedding
        is enabled, returns embedded objects. Otherwise the query set
        will retrieve the objects from the database as needed.
        """
        return MongoDBM2MQuerySet(self.rel, self.objects, use_cached=True)
    
    def ids(self):
        """
        Return a list of ObjectIds of all the related objects.
        """
        return [obj['pk'] for obj in self.objects]
    
    def objs(self):
        """
        Return the actual related model objects, loaded fresh from
        the database. This won't use embedded objects even if they
        exist.
        """
        return MongoDBM2MQuerySet(self.rel, self.objects, use_cached=False)
    
    def to_python_embedded_instance(self, embedded_instance):
        """
        Convert a single embedded instance value stored in the database to an object
        we can store in the internal objects list.
        """
        if self.embed:
            if isinstance(embedded_instance, dict):
                # Convert the embedded value from dict to model
                data = {}
                for field in self.rel._meta.fields:
                    try:
                        data[str(field.attname)] = embedded_instance[field.column]
                    except KeyError:
                        pass
                obj = self.rel(**data)
            else:
                # Assume it's already a model
                obj = embedded_instance
            return {'pk':obj.pk, 'obj':obj}
        else:
            # No embedded value, only ObjectId
            if isinstance(embedded_instance, dict):
                # Get the id value from the dict
                return {'pk':embedded_instance[self.rel._meta.pk.column], 'obj':None}
            else:
                # Assume it's already a model
                return {'pk':embedded_instance.id, 'obj':None}
    
    def to_python(self, values):
        """
        Convert a database value to Django model instances managed by this manager.
        """
        self.objects = [self.to_python_embedded_instance(value) for value in values]
    
    def get_db_prep_value_embedded_instance(self, obj):
        """
        Convert an internal object value to database representation.
        """
        if not obj: return None
        pk = obj['pk']
        if not self.embed:
            # Store only the ID
            return { self.rel._meta.pk.column:pk }
        if not obj['obj']:
            # Retrieve the object from db for storing as embedded data
            obj['obj'] = self.rel.objects.get(pk=pk)
        embedded_instance = obj['obj']
        values = {}
        for field in embedded_instance._meta.fields:
            value = field.pre_save(embedded_instance, add=True)
            value = field.get_db_prep_value(value)
            values[field.column] = value
        # Convert primary key into an ObjectId so it's stored correctly
        values[self.rel._meta.pk.column] = ObjectId(values[self.rel._meta.pk.column])
        return values
    
    def get_db_prep_value(self):
        """
        Convert the Django model instances managed by this manager into a special list
        that can be stored in MongoDB.
        """
        #print 'Manager get_db_prep_value', self.values
        return [self.get_db_prep_value_embedded_instance(obj) for obj in self.objects]

def create_through(model, to):
    # Re-get the to model so that Django recognizes it correctly when verifying the ForeignKeys.
    # The model is not yet gettable because it's being defined right now, but Django won't mind.
    to = models.get_model(to._meta.app_label, to._meta.object_name.lower())
    # Create a dummy 'through' model for MongoDBManyToMany relations. Django assumes there is a real
    # database model providing the relationship, so we simulate it. This model has to have
    # a ForeignKey relationship to both models.
    obj_name = to._meta.object_name + 'Relationship'
    class Through(models.Model):
        class Meta:
            auto_created = True
        locals()[to._meta.object_name.lower()] = models.ForeignKey(to)
        locals()[model._meta.object_name.lower()] = models.ForeignKey(model)
    # Remove old model from Django's model registry, because it would be a duplicate
    from django.db.models.loading import cache
    model_dict = cache.app_models.get(Through._meta.app_label)
    #print Through._meta.app_label, model_dict
    del model_dict[Through._meta.module_name]
    # Rename the model
    Through._meta.object_name = obj_name
    Through._meta.module_name = obj_name.lower()
    Through._meta.db_table = Through._meta.app_label + ' ' + Through._meta.module_name
    Through._meta.verbose_name = to._meta.verbose_name + ' relationship'
    Through._meta.verbose_name_plural = to._meta.verbose_name_plural + ' relationships'
    # Add new model to Django's model registry
    cache.register_models(Through._meta.app_label, Through)
    return Through

class MongoDBManyToManyRelationDescriptor(object):
    """
    This descriptor returns the 'through' model used in Django admin to access the
    ManyToManyField objects for inlines. It's implemented by the MongoDBManyToManyThrough
    class, which simulates a data model. This class also handles the attribute assignment
    from the MongoDB raw fields, which must be properly converted to Python objects.
    """
    def __init__(self, field, through):
        self.field = field
        self.through = through
    
    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = self.field.to_python(value)

class MongoDBManyToManyRel(object):
    """
    This object holds the information of the M2M relationship.
    It's accessed by Django admin/forms in various contexts, and we also
    use it internally. We try to simulate what's needed by Django.
    """
    def __init__(self, field, to, related_name, embed):
        self.model = None # added later from contribute_to_class
        self.through = None # added later from contribute_to_class
        self.field = field
        self.to = to
        self.related_name = related_name
        self.embed = embed
        # Required for Django admin/forms to work.
        self.multiple = True
        self.field_name = self.to._meta.pk.name
        self.limit_choices_to = {}
    
    def is_hidden(self):
        return False

class MongoDBManyToManyField(models.ManyToManyField):#models.Field):
    """
    A generic MongoDB many-to-many field that can store embedded copies of
    the referenced objects. Inherits from djangotoolbox.fields.ListField.
    
    The field's value is a MongoDBM2MRelatedManager object that works similarly to Django's
    RelatedManager objects, so you can add(), remove(), creaet() and clear() on it.
    To access the related object instances, all() is supported. It will return
    all the related instances, using the embedded copies if available.
    
    If you want the 'real' related (non-embedded) model instances, call all_objs() instead.
    If you want the list of related ObjectIds, call all_refs() instead.
    
    The related model will also gain a new accessor method xxx_set() to make reverse queries.
    That accessor is a MongoDBM2MReverseManager that provides an all() method to return
    a QuerySet of related objects.
    
    For example, if you have an Article model with a MongoDBManyToManyField 'categories'
    that refers to Category objects, you will have these methods:
    
    article.categories.all() - Returns all the categories that belong to the article
    category.article_set.all() - Returns all the articles that belong to the category
    """
    #__metaclass__ = models.SubfieldBase
    description = 'ManyToMany field with references and optional embedded objects'
    
    def __init__(self, to, related_name=None, embed=False, default=None, *args, **kwargs):
        # The default value will be an empty MongoDBM2MRelatedManager
        kwargs['default'] = MongoDBM2MRelatedManager(self, to, embed)
        kwargs['rel'] = MongoDBManyToManyRel(self, to, related_name, embed)
        # Call Field, not super, to skip Django's ManyToManyField extra stuff we don't need
        models.Field.__init__(self, *args, **kwargs)
    
    def contribute_to_class(self, model, name, *args, **kwargs):
        self.rel.model = model
        self.rel.through = create_through(self.rel.model, self.rel.to)
        # Call Field, not super, to skip Django's ManyToManyField extra stuff we don't need
        models.Field.contribute_to_class(self, model, name, *args, **kwargs)
        # Determine related name automatically unless set
        if not self.rel.related_name:
            self.rel.related_name = model._meta.object_name.lower() + '_set'
        #if hasattr(self.rel.to, self.rel.related_name):
        #    # Attribute name already taken, raise error
        #    raise Exception(u'Related name ' + unicode(self.rel.to._meta.object_name) + u'.' + unicode(self.rel.related_name) + u' is already used by another field, please choose another name with ' + unicode(name) + u' = ' + unicode(self.__class__.__name__) + u'(related_name=xxx)')
        # Add the reverse relationship
        setattr(self.rel.to, self.rel.related_name, MongoDBM2MReverseDescriptor(model, self, self.rel.to, self.rel.embed))
        # Add the relationship descriptor to the model class for Django admin/forms to work
        setattr(model, self.name, MongoDBManyToManyRelationDescriptor(self, self.rel.through))
    
    def db_type(self, *args, **kwargs):
        return 'list'
    
    def get_db_prep_value(self, value, connection, prepared=False):
        # The Python value is a MongoDBM2MRelatedManager, and we'll store the models it contains as a special list.
        if not isinstance(value, MongoDBM2MRelatedManager):
            # Convert other values to manager objects first
            value = MongoDBM2MRelatedManager(self, self.rel.to, self.rel.embed, value)
        # Let the manager to the conversion
        return value.get_db_prep_value()
    
    def to_python(self, value):
        # The database value is a custom MongoDB list of ObjectIds and embedded models (if embed is enabled).
        # We convert it into a MongoDBM2MRelatedManager object to hold the Django models.
        if not isinstance(value, MongoDBM2MRelatedManager):
            manager = MongoDBM2MRelatedManager(self, self.rel.to, self.rel.embed)
            manager.to_python(value)
            value = manager
        return value
    
#    def formfield(self, **kwargs):
#        return super(MongoDBManyToManyField, self).formfield(**kwargs)
