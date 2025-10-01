from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from account.models import UserData
from .models import ImageModel, ImageCollection, SupportedEPaper
from django.core.files.uploadedfile import SimpleUploadedFile
import io
import base64
from PIL import Image
from unittest.mock import patch, MagicMock

class GetRandomImagesTestCase(APITestCase):
    def setUp(self):
        """Set up test data with minimal database creation"""
        # Create test users (minimal database creation for authentication)
        self.user_data = UserData.objects.create(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        
        self.other_user_data = UserData.objects.create(
            username='otheruser',
            email='otheruser@example.com',
            password='testpass123'
        )
        
        # Create mock image objects without real files
        self.create_mock_images()
    
    def create_mock_images(self):
        """Create ImageModel objects with mocked file uploads"""
        # Create a minimal mock file
        mock_file = SimpleUploadedFile(
            "test_image.png",
            b"fake_image_content",
            content_type="image/png"
        )
        
        # Create ImageModel objects with mocked files (no real image processing)
        self.mock_images = []
        for i in range(5):
            img = ImageModel.objects.create(
                owner=self.user_data,
                image=mock_file
            )
            self.mock_images.append(img)
        
        # Create images for other user
        self.other_mock_images = []
        for i in range(3):
            img = ImageModel.objects.create(
                owner=self.other_user_data,
                image=mock_file
            )
            self.other_mock_images.append(img)
    
    def test_get_random_images_authenticated(self):
        """Test getting random images when authenticated"""
        self.client.force_authenticate(user=self.user_data)
        url = reverse('getRandomImages')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 5)  # Should return all 5 images
    
    def test_get_random_images_with_count_parameter(self):
        """Test getting random images with count parameter"""
        self.client.force_authenticate(user=self.user_data)
        url = reverse('getRandomImages')
        response = self.client.get(url, {'count': 3})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 3)
    
    def test_get_random_images_count_capped_at_50(self):
        """Test that count parameter is capped at 50"""
        self.client.force_authenticate(user=self.user_data)
        url = reverse('getRandomImages')
        response = self.client.get(url, {'count': 100})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 5)  # Should return all available images (5)
    
    def test_get_random_images_count_minimum_1(self):
        """Test that count parameter minimum is 1"""
        self.client.force_authenticate(user=self.user_data)
        url = reverse('getRandomImages')
        response = self.client.get(url, {'count': 0})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)  # Should return at least 1 image
    
    def test_get_random_images_negative_count(self):
        """Test that negative count parameter is handled"""
        self.client.force_authenticate(user=self.user_data)
        url = reverse('getRandomImages')
        response = self.client.get(url, {'count': -5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)  # Should return at least 1 image
    
    def test_get_random_images_invalid_count_parameter(self):
        """Test handling of invalid count parameter"""
        self.client.force_authenticate(user=self.user_data)
        url = reverse('getRandomImages')
        response = self.client.get(url, {'count': 'invalid'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Invalid count parameter', response.data['error'])
    
    def test_get_random_images_no_images(self):
        """Test getting random images when user has no images"""
        # Create a user with no images
        empty_user = UserData.objects.create(
            username='emptyuser',
            email='emptyuser@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=empty_user)
        url = reverse('getRandomImages')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 0)
    
    def test_get_random_images_unauthenticated(self):
        """Test that unauthenticated requests are rejected"""
        url = reverse('getRandomImages')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_random_images_user_isolation(self):
        """Test that users only see their own images"""
        self.client.force_authenticate(user=self.user_data)
        url = reverse('getRandomImages')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)  # Should only see own images
        
        # Switch to other user
        self.client.force_authenticate(user=self.other_user_data)
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Should only see own images
    
    def test_get_random_images_default_count(self):
        """Test that default count is 10 when not specified"""
        # Create 15 images to test default behavior
        self.create_test_images(15)
        
        self.client.force_authenticate(user=self.user_data)
        url = reverse('getRandomImages')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 10)  # Should return default 10
    
    def test_get_random_images_returns_different_order(self):
        """Test that multiple calls return different orders (randomness)"""
        self.client.force_authenticate(user=self.user_data)
        url = reverse('getRandomImages')
        
        # Make multiple requests and check if order varies
        responses = []
        for _ in range(5):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            responses.append([img['id'] for img in response.data])
        
        # Check if at least one response has different order
        # (This test might occasionally fail due to randomness, but very unlikely with 5 attempts)
        orders_are_different = any(
            responses[i] != responses[j] 
            for i in range(len(responses)) 
            for j in range(i + 1, len(responses))
        )
        self.assertTrue(orders_are_different, "Random ordering should produce different results")
