"""
Tests for MongoDBManyToManyField.
"""
from django.test import TestCase
from models import TestArticle, TestCategory, TestTag
import sys

class MongoDBManyToManyFieldTest(TestCase):
    def test_m2m(self):
        # Create some sample data
        category = TestCategory(title='test cat 1')
        category.save()
        category2 = TestCategory(title='test cat 2')
        category2.save()
        category3 = TestCategory(title='test cat 3')
        category3.save()
        category4 = TestCategory(title='test cat 4')
        category4.save()
        tag = TestTag(name='test tag 1')
        tag.save()
        tag2 = TestTag(name='test tag 2')
        tag2.save()
        article = TestArticle(main_category=category, title='test article 1', text='article text')
        article.save()
        article2 = TestArticle(main_category=category, title='test article 2', text='article text 2')
        article2.save()
        article3 = TestArticle(main_category=category, title='test article 3', text='article text 3')
        article3.save()
        # The categories are not embedded, they are stored as relations
        # The tags are embedded
        article.categories.add(category2)
        article.categories.add(category3)
        article.tags.add(tag)
        article.save()
        article2.categories.add(category4)
        article2.tags.add(tag2)
        article2.save()
        article3.categories.add(category4)
        article3.save()
        #sys.stdin.readline()
        # Verify that the categories and tags are loaded correctly
        new_article = TestArticle.objects.get(id=article.id)
        self.assertEquals(new_article.categories.all().count(), 2)
        self.assertEquals(new_article.tags.all().count(), 1)
        self.assertEquals(new_article.main_category.title, 'test cat 1')
        self.assertEquals(new_article.categories.all()[0].title, 'test cat 2')
        self.assertEquals(new_article.categories.all()[1].title, 'test cat 3')
        self.assertEquals(new_article.tags.all()[0].name, 'test tag 1')
        # Verify that the reverse relationship finds the article(s)
        self.assertEquals(tag.articles.all().count(), 1)
        self.assertEquals(tag.articles.all()[0].title, 'test article 1')
        self.assertEquals(category2.testarticle_set.all().count(), 1)
        self.assertEquals(category2.testarticle_set.all()[0].title, 'test article 1')
        self.assertEquals(category3.testarticle_set.all().count(), 1)
        self.assertEquals(category3.testarticle_set.all()[0].title, 'test article 1')
        self.assertEquals(tag2.articles.all().count(), 1)
        self.assertEquals(tag2.articles.all()[0].title, 'test article 2')
        self.assertEquals(category4.testarticle_set.all().count(), 2)
        self.assertEquals(category4.testarticle_set.all()[0].title, 'test article 2')
        self.assertEquals(category4.testarticle_set.all()[1].title, 'test article 3')
