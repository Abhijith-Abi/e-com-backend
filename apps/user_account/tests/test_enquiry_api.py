from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.user_account.models import Enquiry
from datetime import datetime, timedelta

User = get_user_model()


class EnquiryAPITestCase(APITestCase):
    """Test cases for Enquiry API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test user for authentication
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test enquiries
        self.enquiry1 = Enquiry.objects.create(
            name='John Doe',
            mobile='9876543210',
            email='john@example.com',
            company='New York',
            subject='Product Inquiry',
            message='I would like to know more about your products'
        )
        
        self.enquiry2 = Enquiry.objects.create(
            name='Jane Smith',
            mobile='9876543211',
            email='jane@example.com',
            company='Los Angeles',
            subject='Support Request',
            message='I need help with my order'
        )
        
        self.enquiry3 = Enquiry.objects.create(
            name='Bob Johnson',
            mobile='9876543212',
            email='bob@example.com',
            company='New York',
            subject='Feedback',
            message='Great service!'
        )
    
    # List Tests
    def test_list_enquiries_no_auth(self):
        """Test listing enquiries without authentication"""
        response = self.client.get('/api/v1/enquiries/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
    
    def test_list_enquiries_with_pagination(self):
        """Test listing enquiries with pagination"""
        response = self.client.get('/api/v1/enquiries/?page=1&page_size=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_enquiries_sorted_by_date(self):
        """Test that enquiries are sorted by latest date"""
        response = self.client.get('/api/v1/enquiries/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        # Check if sorted by latest date (descending)
        for i in range(len(results) - 1):
            self.assertGreaterEqual(
                results[i]['enquiry_date'],
                results[i + 1]['enquiry_date']
            )
    
    # Retrieve Tests
    def test_retrieve_enquiry_no_auth(self):
        """Test retrieving single enquiry without authentication"""
        response = self.client.get(f'/api/v1/enquiries/{self.enquiry1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'John Doe')
    
    def test_retrieve_nonexistent_enquiry(self):
        """Test retrieving non-existent enquiry"""
        fake_id = '00000000-0000-0000-0000-000000000000'
        response = self.client.get(f'/api/v1/enquiries/{fake_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # Create Tests
    def test_create_enquiry_with_auth(self):
        """Test creating enquiry with authentication"""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'New User',
            'mobile': '9876543213',
            'email': 'newuser@example.com',
            'company': 'Chicago',
            'subject': 'New Inquiry',
            'message': 'Test message'
        }
        response = self.client.post('/api/v1/enquiries/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(Enquiry.objects.count(), 4)
    
    def test_create_enquiry_without_auth(self):
        """Test creating enquiry without authentication"""
        data = {
            'name': 'New User',
            'mobile': '9876543213',
            'email': 'newuser@example.com',
            'company': 'Chicago',
            'subject': 'New Inquiry',
            'message': 'Test message'
        }
        response = self.client.post('/api/v1/enquiries/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_enquiry_with_minimal_data(self):
        """Test creating enquiry with minimal data"""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'Minimal User'
        }
        response = self.client.post('/api/v1/enquiries/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    # Update Tests
    def test_update_enquiry_with_auth(self):
        """Test updating enquiry with authentication"""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'Updated Name',
            'subject': 'Updated Subject'
        }
        response = self.client.patch(f'/api/v1/enquiries/{self.enquiry1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        
        # Verify update
        self.enquiry1.refresh_from_db()
        self.assertEqual(self.enquiry1.name, 'Updated Name')
        self.assertEqual(self.enquiry1.subject, 'Updated Subject')
    
    def test_update_enquiry_without_auth(self):
        """Test updating enquiry without authentication"""
        data = {'name': 'Updated Name'}
        response = self.client.patch(f'/api/v1/enquiries/{self.enquiry1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # Delete Tests
    def test_delete_enquiry_with_auth(self):
        """Test deleting enquiry with authentication"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/v1/enquiries/{self.enquiry1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Enquiry.objects.count(), 2)
    
    def test_delete_enquiry_without_auth(self):
        """Test deleting enquiry without authentication"""
        response = self.client.delete(f'/api/v1/enquiries/{self.enquiry1.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # Filter Tests
    def test_filter_by_name(self):
        """Test filtering enquiries by name"""
        response = self.client.get('/api/v1/enquiries/?name__icontains=John')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'John Doe')
    
    def test_filter_by_city(self):
        """Test filtering enquiries by company"""
        response = self.client.get('/api/v1/enquiries/?company__icontains=New York')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
    
    def test_filter_by_email(self):
        """Test filtering enquiries by email"""
        response = self.client.get('/api/v1/enquiries/?email__icontains=jane')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_filter_by_mobile(self):
        """Test filtering enquiries by mobile"""
        response = self.client.get('/api/v1/enquiries/?mobile__icontains=9876543210')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_filter_by_subject(self):
        """Test filtering enquiries by subject"""
        response = self.client.get('/api/v1/enquiries/?subject__icontains=Support')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_filter_by_is_active(self):
        """Test filtering enquiries by is_active status"""
        response = self.client.get('/api/v1/enquiries/?is_active=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
    
    # Search Tests
    def test_search_enquiries(self):
        """Test searching enquiries"""
        response = self.client.get('/api/v1/enquiries/search/?q=John')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_search_without_query(self):
        """Test search without query parameter"""
        response = self.client.get('/api/v1/enquiries/search/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_search_by_email(self):
        """Test searching by email"""
        response = self.client.get('/api/v1/enquiries/search/?q=jane@example.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    # Date Filter Tests
    def test_filter_by_date_range(self):
        """Test filtering by date range"""
        today = datetime.now().date()
        response = self.client.get(
            f'/api/v1/enquiries/filter_by_date/?from_date={today}&to_date={today}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
    
    # Company Filter Tests
    def test_filter_by_company_endpoint(self):
        """Test filter_by_company custom endpoint"""
        response = self.client.get('/api/v1/enquiries/filter_by_company/?company=New York')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
    
    def test_filter_by_company_without_param(self):
        """Test filter_by_company without company parameter"""
        response = self.client.get('/api/v1/enquiries/filter_by_company/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # Bulk Delete Tests
    def test_bulk_delete_with_auth(self):
        """Test bulk delete with authentication"""
        self.client.force_authenticate(user=self.user)
        data = {
            'ids': [str(self.enquiry1.id), str(self.enquiry2.id)]
        }
        response = self.client.post('/api/v1/enquiries/bulk_delete/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Enquiry.objects.count(), 1)
    
    def test_bulk_delete_without_auth(self):
        """Test bulk delete without authentication"""
        data = {
            'ids': [str(self.enquiry1.id)]
        }
        response = self.client.post('/api/v1/enquiries/bulk_delete/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # Stats Tests
    def test_get_stats(self):
        """Test getting statistics"""
        response = self.client.get('/api/v1/enquiries/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['total_enquiries'], 3)
        self.assertEqual(response.data['data']['active_enquiries'], 3)
        self.assertEqual(response.data['data']['unique_cities'], 2)
    
    # Ordering Tests
    def test_ordering_by_name(self):
        """Test ordering by name"""
        response = self.client.get('/api/v1/enquiries/?ordering=name')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(results[0]['name'], 'Bob Johnson')
    
    def test_ordering_by_date_descending(self):
        """Test ordering by date descending"""
        response = self.client.get('/api/v1/enquiries/?ordering=-enquiry_date')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
