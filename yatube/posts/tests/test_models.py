from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            slug='test-slug',
            title='Тестовый заголовок',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст больше 15 символов',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_models_have_correct_str_names(self):
        group = PostModelTests.group
        expected_object_group_name = group.title
        self.assertEqual(expected_object_group_name, str(group))

        post = PostModelTests.post
        expected_object_post_name = post.text[:15]
        self.assertEqual(expected_object_post_name, str(post))
