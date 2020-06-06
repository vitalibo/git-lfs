import unittest
from pathlib import Path
from unittest import mock

from app import *
from core import *


class SimpleLargeFileStorageTestCase(unittest.TestCase):

    def setUp(self):
        self.mock_repo = mock.MagicMock()
        self.lfs = SimpleLargeFileStorage(
            Path('foo'),
            'https://example.com/'
        )

    def test_exists(self):
        mock_path = mock.MagicMock()
        mock_path.exists.return_value = True
        self.lfs.path = mock.MagicMock()
        self.lfs.path.return_value = mock_path

        actual = self.lfs.exists('happyface.jpg')

        self.assertIsNotNone(actual)
        self.assertTrue(actual)
        self.lfs.path.assert_called_once_with('happyface.jpg')
        mock_path.exists.assert_called_once()

    def test_not_exists(self):
        mock_path = mock.MagicMock()
        mock_path.exists.return_value = False
        self.lfs.path = mock.MagicMock()
        self.lfs.path.return_value = mock_path

        actual = self.lfs.exists('happyface.jpg')

        self.assertIsNotNone(actual)
        self.assertFalse(actual)
        self.lfs.path.assert_called_once_with('happyface.jpg')
        mock_path.exists.assert_called_once()

    def test_path(self):
        actual = self.lfs.path('1bf0e3fc785fde')

        self.assertIsNotNone(actual)
        self.assertEqual(actual, Path('foo/1b/f0/1bf0e3fc785fde'))

    def test_prepare(self):
        actual = self.lfs.prepare('happyface.jpg')

        self.assertIsNotNone(actual)
        self.assertEqual(actual.href, 'https://example.com/transfer/happyface.jpg')

    def test_prepare_download(self):
        actual = self.lfs.prepare_download('happyface.jpg', 123)

        self.assertIsNotNone(actual)
        self.assertEqual(actual.href, 'https://example.com/transfer/happyface.jpg')

    def test_prepare_upload(self):
        actual = self.lfs.prepare_download('happyface.jpg', 123)

        self.assertIsNotNone(actual)
        self.assertEqual(actual.href, 'https://example.com/transfer/happyface.jpg')

    def test_download(self):
        self.lfs.path = mock.MagicMock()
        self.lfs.path.return_value = 'foo'
        with mock.patch('flask.helpers.send_file') as mock_send_file:
            mock_send_file.return_value = 'baz'

            actual = self.lfs.download('happyface.jpg')

            self.assertEqual(actual, 'baz')
            mock_send_file.assert_called_once_with('foo')
            self.lfs.path.assert_called_once_with('happyface.jpg')

    def test_upload(self):
        # TODO: fix me
        self.fail()


class WebAppTestCase(unittest.TestCase):

    def setUp(self):
        Web.app.config['TESTING'] = True
        Web.app.config['DEBUG'] = False
        self.app = Web.app.test_client()

    def tearDown(self):
        pass

    def test_not_found(self):
        response = self.app.get('/foo')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json.get('message'), 'Not found')
        self.assertIsNotNone(response.json.get('request_id'))

    def test_internal_server_error(self):
        with mock.patch('app.Factory.create_batch_facade') as mock_factory:
            mock_facade = mock.MagicMock()
            mock_factory.return_value = mock_facade
            mock_facade.process.side_effect = ValueError()

            response = self.app.post('/objects/batch')

            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json.get('message'), 'Internal Server Error')
            self.assertIsNotNone(response.json.get('request_id'))

    def test_http_error(self):
        with mock.patch('app.Factory.create_batch_facade') as mock_factory:
            mock_facade = mock.MagicMock()
            mock_factory.return_value = mock_facade
            mock_facade.process.side_effect = HttpError(402, 'foo')

            response = self.app.post('/objects/batch')

            self.assertEqual(response.status_code, 402)
            self.assertEqual(response.json.get('message'), 'foo')
            self.assertIsNotNone(response.json.get('request_id'))

    def test_objects_batch(self):
        with mock.patch('app.Factory.create_batch_facade') as mock_factory:
            mock_facade = mock.MagicMock()
            mock_facade.process.return_value = HttpResponse(BatchResponse('foo', []))
            mock_factory.return_value = mock_facade

            response = self.app.post('/objects/batch')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, {'objects': [], 'transfer': 'foo'})

    def test_transfer_get_not_found(self):
        with mock.patch('app.Factory.create_large_file_storage') as mock_factory:
            mock_lfs = mock.MagicMock()
            mock_lfs.exists.return_value = False
            mock_factory.return_value = mock_lfs

            response = self.app.get('/transfer/123')

            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json.get('message'), 'Not found')
            self.assertIsNotNone(response.json.get('request_id'))

    def test_transfer_get(self):
        with mock.patch('app.Factory.create_large_file_storage') as mock_factory:
            mock_lfs = mock.MagicMock()
            mock_lfs.exists.return_value = True
            mock_lfs.download.return_value = 'foo'
            mock_factory.return_value = mock_lfs

            response = self.app.get('/transfer/123')

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, b'foo')
            mock_lfs.exists.assert_called_once_with('123')
            mock_lfs.download.assert_called_once_with('123')

    def test_transfer_put(self):
        with mock.patch('app.Factory.create_large_file_storage') as mock_factory:
            mock_lfs = mock.MagicMock()
            mock_factory.return_value = mock_lfs

            response = self.app.put('/transfer/123')

            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.data, b'')
            mock_lfs.upload.assert_called_once_with('123')
