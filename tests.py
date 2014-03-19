import unittest
import microblog


class MicroblogTest(unittest.TestCase):

    def setUp(self):
        microblog.db.create_all()
        author = microblog.Author('test_auth', 'password', 'email@address.com')
        microblog.db.session.add(author)
        microblog.db.session.commit()

    def test_write_post(self):
        test_title = 'Testing the title.'
        test_body = 'This is the body of the test microblog post.'
        test_cat = ''
        test_auth = 1
        microblog.write_post(test_title, test_body, test_cat, test_auth)
        expected_post = microblog.Post(
            test_title, test_body, [], test_auth)
        result_post = microblog.Post.query.filter_by(title=test_title).first()
        self.assertEqual(expected_post.title, result_post.title)
        self.assertEqual(expected_post.body, expected_post.body)

    def test_read_posts(self):
        test_title = 'Testing the title.'
        test_body = 'This is the body of the test microblog post.'
        test_cat = ''
        test_auth = 1
        microblog.write_post(test_title, test_body, test_cat, test_auth)
        expected_post1 = microblog.Post(
            test_title, test_body, [], test_auth)

        test_title = 'Testing the title a second time.'
        test_body = 'This is the body of the second test microblog post.'
        microblog.write_post(test_title, test_body, test_cat, test_auth)
        expected_post2 = microblog.Post(
            test_title, test_body, [], test_auth)

        results = microblog.read_posts()
        result_post1 = results[1]
        result_post2 = results[0]

        self.assertEqual(expected_post1.title, result_post1.title)
        self.assertEqual(expected_post1.body, result_post1.body)

        self.assertEqual(expected_post2.title, result_post2.title)
        self.assertEqual(expected_post2.body, result_post2.body)

    def test_read_post(self):
        test_title = 'Testing the title.'
        test_body = 'This is the body of the test microblog post.'
        test_cat = ''
        test_auth = 1
        microblog.write_post(test_title, test_body, test_cat, test_auth)
        expected_post = microblog.Post(
            test_title, test_body, [], test_auth)
        result_post = microblog.read_post(1)
        self.assertEqual(expected_post.title, result_post.title)
        self.assertEqual(expected_post.body, result_post.body)

    def tearDown(self):
        microblog.db.session.remove()
        microblog.db.drop_all()

if __name__ == '__main__':
    unittest.main()
