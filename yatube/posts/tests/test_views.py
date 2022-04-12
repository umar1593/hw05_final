from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Comment, Group, Post

User = get_user_model()


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user,
            text='Текст поста',
        )
        cls.comment = Comment.objects.create(
            text='some_text', author=cls.user, post=cls.post
        )
        print(cls.comment.text)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse('posts:profile', args={self.user}): 'posts/profile.html',
            reverse(
                'posts:post_detail', args={self.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for address, template in templates_pages_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def auxiliary_method(self, post):
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author.username, self.user.username)
        self.assertEqual(post.group.title, self.group.title)

    def test_idnex_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.auxiliary_method(first_object)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        self.auxiliary_method(first_object)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', args={self.user})
        )
        first_object = response.context['page_obj'][0]
        self.auxiliary_method(first_object)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args={self.post.pk})
        )
        first_object = response.context['post']
        self.auxiliary_method(first_object)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            )
        )
        first_object = response.context['post']
        self.auxiliary_method(first_object)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_comment_adding_for_authorized_client(self):
        """Проверка добавления комментария к посту."""

        form_data = {
            'comment': self.comment.text,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.post.refresh_from_db()
        first_comment = response.context['comments'][0]
        print(first_comment.text)
        self.assertEqual(first_comment.text, form_data['comment'])

        def test_cache(self):
            with self.assertNumQueries(3):
                response = self.authorized_client.get(reverse('posts:index'))
                self.assertEqual(response.status_code, 200)
                response = self.authorized_client.get(reverse('posts:index'))
                self.assertEqual(response.status_code, 200)
                response = self.authorized_client.get(reverse('posts:index'))
                self.assertEqual(response.status_code, 200)

    # def test_cash_work(self):
    #     """Проверяем кэширование на главной."""
    #     response = self.authorized_client.get(reverse('posts:index'))
    #     first_object = response.content
    #     form_data = {
    #         'title': 'Тестовый заголовок2221111',
    #         'text': 'Тестовый текст22221111',
    #     }
    #     response2 = self.authorized_client.post(
    #         reverse('posts:post_create'), data=form_data, follow=True
    #     )
    #     response = self.authorized_client.get(reverse('posts:index'))
    #     second_object = response.content
    #     self.assertEqual(first_object, second_object)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testAuthor2')
        cls.group = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug-2',
            description='Тестовое описание-2',
        )
        cls.all_posts_count = settings.POSTS_ON_PAGE + 1
        cls.remaining_posts = cls.all_posts_count % settings.POSTS_ON_PAGE
        for i in range(cls.all_posts_count):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Текст {i}',
                group=cls.group,
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        posts_count = len(response.context['page_obj'])
        self.assertEqual(posts_count, settings.POSTS_ON_PAGE)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        posts_count = len(response.context['page_obj'])
        if posts_count < settings.POSTS_ON_PAGE:
            self.assertEqual(posts_count, self.remaining_posts)
        else:
            self.assertEqual(posts_count, settings.POSTS_ON_PAGE)