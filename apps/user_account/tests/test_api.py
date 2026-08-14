from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.user_account.models import (
    Hotel, Package, Houseboat, Cruise, IslandStay,
    FlightEnquiry, Enquiry
)

User = get_user_model()


class BaseAPITestCase(TestCase):
    """Base test case with common setup"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Create regular user
        self.user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='testpass123'
        )


class HotelAPITestCase(BaseAPITestCase):
    """Test cases for Hotel API"""
    
    def setUp(self):
        super().setUp()
        self.hotel = Hotel.objects.create(
            name='Test Hotel',
            slug='test-hotel',
            location='Test Location',
            description='Test Description',
            rating=5,
            price_per_night=1000.00,
            amenities='WiFi,Pool,Spa'
        )
    
    def test_list_hotels(self):
        """Test listing hotels"""
        response = self.client.get('/api/v1/hotels/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # List endpoint returns array directly
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
    
    def test_retrieve_hotel(self):
        """Test retrieving a single hotel"""
        response = self.client.get(f'/api/v1/hotels/{self.hotel.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Retrieve endpoint returns object directly
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data['name'], 'Test Hotel')
    
    def test_create_hotel_as_admin(self):
        """Test creating hotel as admin"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'New Hotel',
            'slug': 'new-hotel',
            'location': 'New Location',
            'description': 'New Description',
            'rating': 4,
            'price_per_night': 2000.00
        }
        response = self.client.post('/api/v1/hotels/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
    
    def test_create_hotel_as_user_fails(self):
        """Test creating hotel as regular user fails"""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'New Hotel',
            'slug': 'new-hotel',
            'location': 'New Location',
            'description': 'New Description',
            'rating': 4,
            'price_per_night': 2000.00
        }
        response = self.client.post('/api/v1/hotels/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_hotel(self):
        """Test updating hotel"""
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'Updated Hotel'}
        response = self.client.patch(f'/api/v1/hotels/{self.hotel.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['name'], 'Updated Hotel')
    
    def test_delete_hotel(self):
        """Test deleting hotel (soft delete)"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/v1/hotels/{self.hotel.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify soft delete
        self.hotel.refresh_from_db()
        self.assertFalse(self.hotel.is_active)
    
    def test_featured_hotels(self):
        """Test featured hotels endpoint"""
        self.hotel.is_featured = True
        self.hotel.save()
        
        response = self.client.get('/api/v1/hotels/featured/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertEqual(len(response.data['data']), 1)


class PackageAPITestCase(BaseAPITestCase):
    """Test cases for Package API"""
    
    def setUp(self):
        super().setUp()
        self.package = Package.objects.create(
            title='Test Package',
            slug='test-package',
            location='Test Location',
            description='Test Description',
            duration='5 Days / 4 Nights',
            group_size='2-6 Pax',
            price=50000.00,
            original_price=60000.00,
            category='international',
            type='international',
            is_international=True
        )
    
    def test_list_packages(self):
        """Test listing packages"""
        response = self.client.get('/api/v1/packages/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # List endpoint returns array directly
        self.assertIsInstance(response.data, list)
    
    def test_filter_packages_by_type(self):
        """Test filtering packages by type"""
        response = self.client.get('/api/v1/packages/?type=international')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # List endpoint returns array directly
        self.assertIsInstance(response.data, list)
        if len(response.data) > 0:
            self.assertEqual(response.data[0]['type'], 'international')
    
    def test_kerala_packages(self):
        """Test Kerala packages endpoint"""
        kerala_package = Package.objects.create(
            title='Kerala Package',
            slug='kerala-package',
            location='Kerala',
            description='Kerala Description',
            duration='3 Days / 2 Nights',
            group_size='2-4 Pax',
            price=25000.00,
            category='kerala',
            type='kerala',
            is_kerala=True
        )
        
        response = self.client.get('/api/v1/packages/kerala/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertGreaterEqual(len(response.data['data']), 1)


class FlightEnquiryAPITestCase(BaseAPITestCase):
    """Test cases for Flight Enquiry API"""
    
    def test_create_flight_enquiry(self):
        """Test creating flight enquiry without authentication"""
        data = {
            'trip_type': 'roundtrip',
            'from_location': 'Mumbai',
            'to_location': 'Dubai',
            'departure_date': '2024-12-01',
            'return_date': '2024-12-10',
            'adults': 2,
            'children': 0,
            'travel_class': 'economy',
            'name': 'John Doe',
            'phone': '+919876543210',
            'email': 'john@example.com'
        }
        response = self.client.post('/api/v1/flight-enquiries/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
    
    def test_create_flight_enquiry_validation(self):
        """Test flight enquiry validation"""
        data = {
            'trip_type': 'roundtrip',
            'from_location': 'Mumbai',
            'to_location': 'Dubai',
            'departure_date': '2024-12-01',
            # Missing return_date for roundtrip
            'adults': 2,
            'name': 'John Doe',
            'phone': '+919876543210',
            'email': 'john@example.com'
        }
        response = self.client.post('/api/v1/flight-enquiries/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
    
    def test_list_flight_enquiries_requires_auth(self):
        """Test listing flight enquiries requires authentication"""
        response = self.client.get('/api/v1/flight-enquiries/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_flight_enquiry_status(self):
        """Test updating flight enquiry status as admin"""
        enquiry = FlightEnquiry.objects.create(
            trip_type='oneway',
            from_location='Delhi',
            to_location='London',
            departure_date='2024-12-15',
            adults=1,
            travel_class='business',
            name='Jane Doe',
            phone='+919876543210',
            email='jane@example.com'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        data = {'status': 'contacted'}
        response = self.client.patch(f'/api/v1/flight-enquiries/{enquiry.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['status'], 'contacted')


class EnquiryAPITestCase(BaseAPITestCase):
    """Test cases for General Enquiry API"""
    
    def test_create_enquiry(self):
        """Test creating general enquiry"""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+919876543210',
            
            'service': 'packages-kerala',
            'destination': 'Munnar',
            'travel_date': '2024-12-20',
            'travelers': '2',
            'message': 'Looking for a Kerala honeymoon package'
        }
        response = self.client.post('/api/v1/enquiries/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
    
    def test_create_enquiry_validation(self):
        """Test enquiry validation"""
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+919876543210',
            'service': 'hotels',
            'message': 'Short'  # Too short
        }
        response = self.client.post('/api/v1/enquiries/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
    
    def test_filter_enquiries_by_service(self):
        """Test filtering enquiries by service"""
        Enquiry.objects.create(
            name='User 1',
            email='user1@example.com',
            phone='+919876543210',
            service='hotels',
            message='Looking for hotels in Maldives'
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/enquiries/by_service/?service=hotels')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)


class UserAPITestCase(BaseAPITestCase):
    """Test cases for User API"""
    
    def test_get_current_user(self):
        """Test getting current user profile"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['username'], 'testuser')
    
    def test_change_password(self):
        """Test changing password"""
        self.client.force_authenticate(user=self.user)
        data = {
            'old_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        response = self.client.post('/api/v1/users/change_password/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify password changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
    
    def test_change_password_wrong_old_password(self):
        """Test changing password with wrong old password"""
        self.client.force_authenticate(user=self.user)
        data = {
            'old_password': 'wrongpass',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        response = self.client.post('/api/v1/users/change_password/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)
    
    def test_logout(self):
        """Test logout"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/users/logout/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
