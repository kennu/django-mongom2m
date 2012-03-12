from django.contrib import admin
import models

class TestCategoryAdmin(admin.ModelAdmin):
    list_display = ['title']

class TestTagAdmin(admin.ModelAdmin):
    list_display = ['name']

class TestCategoryInline(admin.TabularInline):
    model = models.TestArticle.categories.through

class TestArticleAdmin(admin.ModelAdmin):
    list_display = ['title']
    search_fields = ['title']
    exclude = ['categories']
    inlines = [ TestCategoryInline ]

class TestAuthorAdmin(admin.ModelAdmin):
    list_display = ['name']

class TestBookAdmin(admin.ModelAdmin):
    raw_id_fields = ['authors']

admin.site.register(models.TestCategory, TestCategoryAdmin)
admin.site.register(models.TestTag, TestTagAdmin)
admin.site.register(models.TestArticle, TestArticleAdmin)
admin.site.register(models.TestAuthor, TestAuthorAdmin)
admin.site.register(models.TestBook, TestBookAdmin)
