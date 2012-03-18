from django.test import TestCase
from django.db import models
from mongom2m.fields import MongoDBManyToManyField
from django_mongodb_engine.contrib import MongoDBManager
from djangotoolbox.fields import ListField, EmbeddedModelField
from models import TestArticle, TestCategory, TestTag, TestAuthor, TestBook#, TestOldArticle, TestOldEmbeddedArticle
from pymongo.objectid import ObjectId
import sys

class MongoDBManyToManyFieldTest(TestCase):
    def test_m2m(self):
        """
        Test general M2M functionality.
        """
        # Create some sample data
        category1 = TestCategory(title='test cat 1')
        category1.save()
        category2 = TestCategory(title='test cat 2')
        category2.save()
        category3 = TestCategory(title='test cat 3')
        category3.save()
        category4 = TestCategory(title='test cat 4')
        category4.save()
        tag1 = TestTag(name='test tag 1')
        tag1.save()
        tag2 = TestTag(name='test tag 2')
        tag2.save()
        article = TestArticle(main_category=category1, title='test article 1', text='article text')
        article.save()
        article2 = TestArticle(main_category=category1, title='test article 2', text='article text 2')
        article2.save()
        article3 = TestArticle(main_category=category1, title='test article 3', text='article text 3')
        article3.save()
        # The categories are not embedded, they are stored as relations
        # The tags are embedded
        article.categories.add(category2)
        article.categories.add(category3)
        article.tags.add(tag1)
        article.save()
        article2.categories.add(category4)
        article2.tags.add(tag2)
        article2.save()
        article3.categories.add(category4)
        article3.save()
        #sys.stdin.readline()
        new_article = TestArticle.objects.get(id=article.id)
        # Verify that the ObjectIds pk's are converted to strings to be compatible with django-mongodb-engine
        self.assertIsInstance(new_article.categories.all()[0].id, basestring)
        self.assertIsInstance(new_article.tags.all()[0].id, basestring)
        # Verify that the categories and tags are loaded correctly
        self.assertEqual(new_article.categories.all().count(), 2)
        self.assertEqual(new_article.tags.all().count(), 1)
        self.assertEqual(new_article.main_category.title, 'test cat 1')
        self.assertEqual(new_article.categories.all()[0].title, 'test cat 2')
        self.assertEqual(new_article.categories.all()[1].title, 'test cat 3')
        self.assertEqual(new_article.tags.all()[0].name, 'test tag 1')
        # Verify that the reverse relationship finds the article(s)
        self.assertEqual(tag1.articles.all().count(), 1)
        self.assertEqual(tag1.articles.all()[0].title, 'test article 1')
        self.assertEqual(category2.testarticle_set.all().count(), 1)
        self.assertEqual(category2.testarticle_set.all()[0].title, 'test article 1')
        self.assertEqual(category3.testarticle_set.all().count(), 1)
        self.assertEqual(category3.testarticle_set.all()[0].title, 'test article 1')
        self.assertEqual(tag2.articles.all().count(), 1)
        self.assertEqual(tag2.articles.all()[0].title, 'test article 2')
        self.assertEqual(category4.testarticle_set.all().count(), 2)
        self.assertEqual(category4.testarticle_set.all()[0].title, 'test article 2')
        self.assertEqual(category4.testarticle_set.all()[1].title, 'test article 3')
    
    def test_migrations(self):
        """
        Test migrating from an existing ListField(ForeignKey) field
        """
        # Create test categories
        category1 = TestCategory(title='test cat 1')
        category1.save()
        category2 = TestCategory(title='test cat 2')
        category2.save()
        # Create test tags
        tag1 = TestTag(name='test tag 1')
        tag1.save()
        tag2 = TestTag(name='test tag 2')
        tag2.save()
        
        # Create the old data - this model uses ListField(ForeignKey) fields
        class TestOldArticle(models.Model):
            class Meta:
                # Used for testing migrations using same MongoDB collection
                db_table = 'mongom2m_testapp_testarticle'
            
            objects = MongoDBManager()
            main_category = models.ForeignKey(TestCategory, related_name='main_oldarticles')
            categories = ListField(models.ForeignKey(TestCategory))
            tags = ListField(models.ForeignKey(TestTag))
            title = models.CharField(max_length=254)
            text = models.TextField()
            
            def __unicode__(self):
                return self.title
        
        old_article = TestOldArticle(title='old article 1', text='old article text 1', main_category=category1, categories=[category1.id, category2.id], tags=[tag1.id, tag2.id])
        old_article.save()
        
        # Now use the new model to access the old data.
        new_article = TestArticle.objects.get(title='old article 1')
        
        # Make sure the fields were loaded correctly
        self.assertEqual(set(cat.title for cat in new_article.categories.all()), set(('test cat 1', 'test cat 2')))
        self.assertEqual(set(cat.id for cat in new_article.categories.all()), set((category1.id, category2.id)))
        self.assertEqual(set(tag.name for tag in new_article.tags.all()), set(('test tag 1', 'test tag 2')))
        self.assertEqual(set(tag.id for tag in new_article.tags.all()), set((tag1.id, tag2.id)))
        
        # Re-save and reload the data to migrate it in MongoDB
        new_article.save()
        migrated_article = TestArticle.objects.get(title='old article 1')
        
        # Make sure the fields are still loaded correctly
        self.assertEqual(set(cat.title for cat in migrated_article.categories.all()), set(('test cat 1', 'test cat 2')))
        self.assertEqual(set(cat.id for cat in migrated_article.categories.all()), set((category1.id, category2.id)))
        self.assertEqual(set(tag.name for tag in migrated_article.tags.all()), set(('test tag 1', 'test tag 2')))
        self.assertEqual(set(tag.id for tag in migrated_article.tags.all()), set((tag1.id, tag2.id)))
    
    def test_embedded_migrations(self):
        """
        Test migrating from an existing ListField(EmbeddedModelField)
        """
        # Create test categories
        category1 = TestCategory(title='test cat 1')
        category1.save()
        category2 = TestCategory(title='test cat 2')
        category2.save()
        # Create test tags
        tag1 = TestTag(name='test tag 1')
        tag1.save()
        tag2 = TestTag(name='test tag 2')
        tag2.save()
        
        # Create the old data - this model uses ListField(EmbeddedModelField) fields
        class TestOldEmbeddedArticle(models.Model):
            class Meta:
                # Used for testing migrations using same MongoDB collection
                db_table = 'mongom2m_testapp_testarticle'
            
            objects = MongoDBManager()
            main_category = models.ForeignKey(TestCategory, related_name='main_oldembeddedarticles')
            categories = ListField(EmbeddedModelField(TestCategory))
            tags = ListField(EmbeddedModelField(TestTag))
            title = models.CharField(max_length=254)
            text = models.TextField()
            
            def __unicode__(self):
                return self.title
        
        old_article = TestOldEmbeddedArticle(title='old embedded article 1', text='old embedded article text 1', main_category=category1, categories=[category1, category2], tags=[tag1, tag2])
        old_article.save()
        
        # Now use the new model to access the old data.
        new_article = TestArticle.objects.get(title='old embedded article 1')
        
        # Make sure the fields were loaded correctly
        self.assertEqual(set(cat.title for cat in new_article.categories.all()), set(('test cat 1', 'test cat 2')))
        self.assertEqual(set(cat.id for cat in new_article.categories.all()), set((category1.id, category2.id)))
        self.assertEqual(set(tag.name for tag in new_article.tags.all()), set(('test tag 1', 'test tag 2')))
        self.assertEqual(set(tag.id for tag in new_article.tags.all()), set((tag1.id, tag2.id)))
        
        # Re-save and reload the data to migrate it in MongoDB
        new_article.save()
        migrated_article = TestArticle.objects.get(title='old embedded article 1')
        
        # Make sure the fields are still loaded correctly
        self.assertEqual(set(cat.title for cat in migrated_article.categories.all()), set(('test cat 1', 'test cat 2')))
        self.assertEqual(set(cat.id for cat in migrated_article.categories.all()), set((category1.id, category2.id)))
        self.assertEqual(set(tag.name for tag in migrated_article.tags.all()), set(('test tag 1', 'test tag 2')))
        self.assertEqual(set(tag.id for tag in migrated_article.tags.all()), set((tag1.id, tag2.id)))
    
    def test_signals(self):
        """
        Test signals emitted by various M2M operations.
        """

