import datetime
import unittest
from unittest import mock

from core import HttpResponse, BatchResponse, HttpError
from main import *


class GoogleCloudFileStorageTestCase(unittest.TestCase):

    def setUp(self):
        with mock.patch('google.cloud.storage.Client') as mock_storage_client:
            mock_storage_client.return_value = mock.MagicMock()
            self.lfs = GoogleCloudFileStorage()
            self.bucket_mock = mock.MagicMock()
            self.blob_mock = mock.MagicMock()
            self.bucket_mock.blob.return_value = self.blob_mock
            self.lfs.bucket = self.bucket_mock

    def test_exists(self):
        self.blob_mock.exists.return_value = True

        actual = self.lfs.exists('foo')

        self.assertTrue(actual)
        self.bucket_mock.blob.assert_called_once_with('foo')
        self.blob_mock.exists.assert_called_once()

    def test_not_exists(self):
        self.blob_mock.exists.return_value = False

        actual = self.lfs.exists('foo')

        self.assertFalse(actual)
        self.bucket_mock.blob.assert_called_once_with('foo')
        self.blob_mock.exists.assert_called_once()

    def test_presign(self):
        self.blob_mock.generate_signed_url.return_value = 'http://examplebucket/happyface.jpg'

        actual = self.lfs.presign('GET/PUT', 'happyface.jpg')

        self.assertIsNotNone(actual)
        self.assertEqual(actual, 'http://examplebucket/happyface.jpg')
        self.bucket_mock.blob.assert_called_once_with('happyface.jpg')
        self.blob_mock.generate_signed_url.assert_called_once_with(
            version='v4',
            expiration=datetime.timedelta(minutes=60),
            method='GET/PUT'
        )

    def test_prepare_download(self):
        self.lfs.presign = mock.MagicMock()
        self.lfs.presign.return_value = 'http://examplebucket/happyface.jpg?action=get_object'

        actual = self.lfs.prepare_download('happyface.jpg', 123)

        self.assertIsNotNone(actual)
        self.assertEqual(actual.href, 'http://examplebucket/happyface.jpg?action=get_object')
        self.lfs.presign.assert_called_once_with('GET', 'happyface.jpg')

    def test_prepare_upload(self):
        self.lfs.presign = mock.MagicMock()
        self.lfs.presign.return_value = 'http://examplebucket/happyface.jpg?action=put_object'

        actual = self.lfs.prepare_upload('happyface.jpg', 123)

        self.assertIsNotNone(actual)
        self.assertEqual(actual.href, 'http://examplebucket/happyface.jpg?action=put_object')
        self.lfs.presign.assert_called_once_with('PUT', 'happyface.jpg')


class FunctionTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.mock_request = mock.MagicMock()
        self.mock_request.path = '/objects/batch'
        self.mock_request.method = 'GET'
        self.mock_request.json = '{"a":"b"}'
        self.mock_facade = mock.MagicMock()

    def test_process(self):
        with mock.patch('main.Factory.create_batch_facade') as mock_factory:
            mock_factory.return_value = self.mock_facade
            self.mock_facade.process.return_value = HttpResponse(BatchResponse('foo', []))

            actual = process(self.mock_request)

            self.assertIsNotNone(actual)
            self.assertEqual(actual[0], {'objects': [], 'transfer': 'foo'})
            self.assertEqual(actual[1], 200)

    def test_process_http_error(self):
        with mock.patch('main.Factory.create_batch_facade') as mock_factory, \
                mock.patch('uuid.uuid4') as mock_uuid:
            mock_factory.return_value = self.mock_facade
            self.mock_facade.process.side_effect = HttpError(123, 'foo')
            mock_uuid.return_value = 'uuid'

            actual = process(self.mock_request)

            self.assertIsNotNone(actual)
            self.assertEqual(actual[0], {'message': 'foo', 'request_id': 'uuid'})
            self.assertEqual(actual[1], 123)

    def test_process_internal_server_error(self):
        with mock.patch('main.Factory.create_batch_facade') as mock_factory, \
                mock.patch('uuid.uuid4') as mock_uuid:
            mock_factory.return_value = self.mock_facade
            self.mock_facade.process.side_effect = KeyError('foo')
            mock_uuid.return_value = 'uuid'

            actual = process(self.mock_request)

            self.assertIsNotNone(actual)
            self.assertEqual(actual[0], {'message': 'Internal Server Error', 'request_id': 'uuid'})
            self.assertEqual(actual[1], 500)
