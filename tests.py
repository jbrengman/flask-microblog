import unittest
import microblog


class MicroblogTest(unittest.TestCase):

    def setUp(self):
        microblog.db.create_all()

    def test_write_post(self):
        test_title = 'Testing the title.'
        test_body = 'This is the body of the test microblog post.'
        microblog.write_post(test_title, test_body)
        expected_post = microblog.Post(test_title, test_body)
        result_post = microblog.Post.query.filter_by(title=test_title).first()
        self.assertEqual(expected_post.title, result_post.title)
        self.assertEqual(expected_post.body, expected_post.body)

    def test_read_posts(self):
        test_title = 'Testing the title.'
        test_body = 'This is the body of the test microblog post.'
        microblog.write_post(test_title, test_body)
        expected_post = microblog.Post(test_title, test_body)
        result_post = microblog.read_posts()[0]
        self.assertEqual(expected_post.title, result_post.title)
        self.assertEqual(expected_post.body, result_post.body)

        test_title = 'Testing the title a second time.'
        test_body = 'This is the body of the second test microblog post.'
        microblog.write_post(test_title, test_body)
        expected_post = microblog.Post(test_title, test_body)
        result_post = microblog.read_posts()[1]
        self.assertEqual(expected_post.title, result_post.title)
        self.assertEqual(expected_post.body, result_post.body)

    def test_read_post(self):
        test_title = 'Testing the title.'
        test_body = 'This is the body of the test microblog post.'
        microblog.write_post(test_title, test_body)
        expected_post = microblog.Post(test_title, test_body)
        result_post = microblog.read_post(1)
        self.assertEqual(expected_post.title, result_post.title)
        self.assertEqual(expected_post.body, result_post.body)

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

if __name__ == '__main__':
    unittest.main()
