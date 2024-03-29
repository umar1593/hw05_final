import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            slug='test-slug',
            title='Тестовый заголовок',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif', content=cls.small_gif, content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post.."""
        post_count = Post.objects.count()

        uploaded = SimpleUploadedFile(
            name='small1.gif', content=self.small_gif, content_type='image/gif'
        )
        form_data = {
            'text': 'the new text',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username}),
        )
        post = Post.objects.all().order_by('-id')[0]
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.post.refresh_from_db()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group_id, form_data['group'])
        self.assertEqual(post.image.name, 'posts/' + uploaded.name)

    def test_edit_post(self):
        """Проверка сохранения поста после редактирования."""

        uploaded = SimpleUploadedFile(
            name='small2.gif', content=self.small_gif, content_type='image/gif'
        )
        form_data = {
            'text': 'the another text',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args={self.post.pk}),
        )

        self.post.refresh_from_db()
        self.assertEqual(self.post.text, form_data['text'])
        self.assertEqual(self.post.group.pk, form_data['group'])
        self.assertEqual(self.post.image.name, 'posts/' + uploaded.name)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_foller = User.objects.create_user(username='Подписчик')
        cls.user_folling = User.objects.create_user(username='Автор')
        cls.count = Follow.objects.filter(
            user=cls.user_foller, author=cls.user_folling
        ).count()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client_foller = Client()
        self.authorized_client_folling = Client()
        self.authorized_client_foller.force_login(self.user_foller)
        self.authorized_client_folling.force_login(self.user_folling)

    def test_follow(self):
        Post.objects.create(
            text='Тестовый пост 4564534', author=self.user_foller
        )
        Post.objects.create(
            text='Тестовый пост 9789', author=self.user_folling
        )
        Post.objects.create(
            text='Тестовый пост 4574', author=self.user_folling
        )
        self.authorized_client_foller.get(
            reverse('posts:profile_follow', args={self.user_folling.username})
        )
        self.count = Follow.objects.filter(
            user=self.user_foller, author=self.user_folling
        ).count()
        self.assertEqual(self.count, 1)
        response = self.authorized_client_foller.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_unfollow(self):
        self.authorized_client_foller.get(
            reverse(
                'posts:profile_unfollow', args={self.user_folling.username}
            )
        )
        self.count = Follow.objects.filter(
            user=self.user_foller, author=self.user_folling
        ).count()
        self.assertEqual(self.count, 0)
