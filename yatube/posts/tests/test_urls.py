from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Comment, Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст поста',
        )
        cls.comment = Comment.objects.create(
            text='some_text', author=cls.user, post=cls.post
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_the_urls_exists_at_desired_locations(self):
        """Страница словаря urls доступнs пользователям."""
        urls = {
            'one': self.client.get('/'),
            'two': self.client.get(f'/group/{self.group.slug}/'),
            'three': self.client.get(f'/profile/{self.user}/'),
            'four': self.client.get(f'/posts/{self.post.id}/'),
            'five': self.authorized_client.get(f'/posts/{self.post.id}/edit/'),
            'six': self.authorized_client.get('/create/'),
        }
        for name, address in urls.items():
            with self.subTest(address=address):
                response = address
                self.assertEqual(response.status_code, 200)

    def test_post_edit_url_redirect_anonymous(self):
        """Страница /post_id/edit перенаправляет анонимного пользователя."""
        response = self.client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_post_create_url_redirect_anonymous(self):
        """Страница /posts/create/ перенаправляет анонимного пользователя."""
        response = self.client.get('/create/', follow=True)
        self.assertRedirects(response, ('/auth/login/?next=/create/'))

    def test_unexisting_page(self):
        """Запрос к страница unixisting_page вернет ошибку 404"""
        response = self.client.get('/unixisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_add_comment_url_redirect_user(self):
        """Страница posts/<int:post_id>/comment/ перенаправляет
        authorized_clientна posts:post_detail."""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/comment/'
        )
        self.assertRedirects(response, (f'/posts/{self.post.id}/'))
        self.assertEqual(response.status_code, 302)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
