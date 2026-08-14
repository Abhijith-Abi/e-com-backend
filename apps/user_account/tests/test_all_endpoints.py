"""
Comprehensive test to verify all API endpoints are working
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.user_account.models import (
    Hotel, Package, Houseboat, Cruise, IslandStay
)

User = get_user_model()


class AllEndpointsTestCase(TestCase):
    """Test all API endpoints to verify they're working"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='user123'
        )
        
        # Create test data
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            slug='test-hotel',
            location='Mumbai',
            rating=5,
            price_per_night=5000.00
        )
        
        self.package = Package.objects.create(
            title='Test Package',
            slug='test-package',
            location='Kerala',
            duration='5 Days',
            price=50000.00,
            category='kerala',
            type='kerala',
            is_kerala=True
        )
        
        self.houseboat = Houseboat.objects.create(
            name='Test Houseboat',
            slug='test-houseboat',
            type='deluxe',
            capacity=4,
            bedrooms=2,
            route='Alleppey',
            duration='1 Day',
            price=15000.00
        )
        
        self.cruise = Cruise.objects.create(
            name='Test Cruise',
            slug='test-cruise',
            cruise_line='Test Line',
            route='Mumbai-Goa',
            duration='3 Days',
            price=25000.00
        )
        
        self.island_stay = IslandStay.objects.create(
            name='Test Island',
            slug='test-island',
            location='Maldives',
            rating=5,
            price=80000.00,
            duration='4 Days'
        )
    
    def test_authentication_endpoints(self):
        """Test authentication endpoints"""
        # Login
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'testuser',
            'password': 'user123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('tokens', response.data['data'])
        
        # Verify token
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/auth/verify/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_hotel_endpoints(self):
        """Test all hotel endpoints"""
        # List
        response = self.client.get('/api/v1/hotels/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Detail
        response = self.client.get(f'/api/v1/hotels/{self.hotel.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Featured
        response = self.client.get('/api/v1/hotels/featured/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Trending
        response = self.client.get('/api/v1/hotels/trending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_package_endpoints(self):
        """Test all package endpoints"""
        # List
        response = self.client.get('/api/v1/packages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Detail
        response = self.client.get(f'/api/v1/packages/{self.package.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Featured
        response = self.client.get('/api/v1/packages/featured/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Trending
        response = self.client.get('/api/v1/packages/trending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Kerala
        response = self.client.get('/api/v1/packages/kerala/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # International
        response = self.client.get('/api/v1/packages/international/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_houseboat_endpoints(self):
        """Test all houseboat endpoints"""
        # List
        response = self.client.get('/api/v1/houseboats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Detail
        response = self.client.get(f'/api/v1/houseboats/{self.houseboat.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Featured
        response = self.client.get('/api/v1/houseboats/featured/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Trending
        response = self.client.get('/api/v1/houseboats/trending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_cruise_endpoints(self):
        """Test all cruise endpoints"""
        # List
        response = self.client.get('/api/v1/cruises/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Detail
        response = self.client.get(f'/api/v1/cruises/{self.cruise.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Featured
        response = self.client.get('/api/v1/cruises/featured/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Trending
        response = self.client.get('/api/v1/cruises/trending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_island_stay_endpoints(self):
        """Test all island stay endpoints"""
        # List
        response = self.client.get('/api/v1/island-stays/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Detail
        response = self.client.get(f'/api/v1/island-stays/{self.island_stay.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Featured
        response = self.client.get('/api/v1/island-stays/featured/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Trending
        response = self.client.get('/api/v1/island-stays/trending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_flight_enquiry_endpoints(self):
        """Test flight enquiry endpoints"""
        # Create (public)
        response = self.client.post('/api/v1/flight-enquiries/', {
            'trip_type': 'oneway',
            'from_location': 'Mumbai',
            'to_location': 'Dubai',
            'departure_date': '2024-12-01',
            'adults': 2,
            'travel_class': 'economy',
            'name': 'Test User',
            'phone': '+919876543210',
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # List (requires auth)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/v1/flight-enquiries/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Pending
        response = self.client.get('/api/v1/flight-enquiries/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # By status
        response = self.client.get('/api/v1/flight-enquiries/by_status/?status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_enquiry_endpoints(self):
        """Test general enquiry endpoints"""
        # Create (public)
        response = self.client.post('/api/v1/enquiries/', {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+919876543210',
            'service': 'hotels',
            'message': 'Looking for hotels in Goa for vacation'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # List (requires auth)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/v1/enquiries/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Pending
        response = self.client.get('/api/v1/enquiries/pending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # By status
        response = self.client.get('/api/v1/enquiries/by_status/?status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # By service
        response = self.client.get('/api/v1/enquiries/by_service/?service=hotels')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_endpoints(self):
        """Test user endpoints"""
        self.client.force_authenticate(user=self.user)
        
        # Get current user
        response = self.client.get('/api/v1/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Change password
        response = self.client.post('/api/v1/users/change_password/', {
            'old_password': 'user123',
            'new_password': 'newpass456',
            'confirm_password': 'newpass456'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Logout
        response = self.client.post('/api/v1/users/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
