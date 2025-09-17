import pytest
import json
from unittest.mock import patch, MagicMock
from main.app import app
from main.database.models import db


class TestWardCandidatesAPI:
    """Test cases for the ward candidates API endpoint."""
    
    def setup_method(self):
        """Set up test client and mock data."""
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True
        
        # Mock candidate data
        self.mock_candidates = [
            {
                'id': '1',
                'name': 'John Doe',
                'party': 'Democratic Party',
                'orderno': '1',
                'ward_code': 'WARD001',
                'candidate_type': 'ward'
            },
            {
                'id': '2',
                'name': 'Jane Smith',
                'party': 'Republican Party',
                'orderno': '2',
                'ward_code': 'WARD001',
                'candidate_type': 'ward'
            }
        ]
        
        # Mock ward data
        self.mock_wards = [
            {'ward_id': 'WARD001'},
            {'ward_id': 'WARD002'},
            {'ward_id': 'WARD003'}
        ]

    @patch('main.api_routes.get_candidates_by_ward_id')
    def test_get_ward_candidates_success(self, mock_get_candidates):
        """Test successful retrieval of ward candidates."""
        mock_get_candidates.return_value = self.mock_candidates
        
        response = self.client.get('/api/v1/wards/WARD001/candidates')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['ward_id'] == 'WARD001'
        assert data['candidate_type'] == 'ward'
        assert len(data['candidates']) == 2
        assert data['count'] == 2
        assert data['candidates'][0]['name'] == 'John Doe'
        assert data['candidates'][1]['name'] == 'Jane Smith'

    @patch('main.api_routes.get_candidates_by_ward_id')
    def test_get_ward_candidates_with_candidate_type(self, mock_get_candidates):
        """Test retrieval with specific candidate type."""
        mock_get_candidates.return_value = self.mock_candidates
        
        response = self.client.get('/api/v1/wards/WARD001/candidates?candidate_type=municipal')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['candidate_type'] == 'municipal'
        mock_get_candidates.assert_called_once_with('WARD001', 'municipal')

    @patch('main.api_routes.get_candidates_by_ward_id')
    def test_get_ward_candidates_empty_result(self, mock_get_candidates):
        """Test retrieval when no candidates found."""
        mock_get_candidates.return_value = []
        
        response = self.client.get('/api/v1/wards/WARD999/candidates')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['ward_id'] == 'WARD999'
        assert data['candidates'] == []
        assert data['count'] == 0
        assert 'No candidates found' in data['message']

    def test_get_ward_candidates_invalid_ward_id(self):
        """Test with invalid ward ID."""
        response = self.client.get('/api/v1/wards//candidates')
        
        assert response.status_code == 404  # Flask returns 404 for empty path parameter

    @patch('main.api_routes.get_candidates_by_ward_id')
    def test_get_ward_candidates_database_error(self, mock_get_candidates):
        """Test handling of database errors."""
        mock_get_candidates.side_effect = Exception("Database connection error")
        
        response = self.client.get('/api/v1/wards/WARD001/candidates')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        
        assert data['error'] == 'Internal server error'
        assert 'An error occurred while retrieving candidates' in data['message']

    @patch('main.api_routes.get_ward_code_for_candidate_type')
    def test_get_ward_candidates_no_ward_code(self, mock_get_ward_code):
        """Test when ward code cannot be determined."""
        mock_get_ward_code.return_value = None
        
        response = self.client.get('/api/v1/wards/WARD001/candidates')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['candidates'] == []


class TestAvailableWardsAPI:
    """Test cases for the available wards API endpoint."""
    
    def setup_method(self):
        """Set up test client."""
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True

    @patch('main.api_routes.db.session.execute')
    def test_get_available_wards_success(self, mock_execute):
        """Test successful retrieval of available wards."""
        # Mock the database result
        mock_result = MagicMock()
        mock_result.__iter__ = lambda self: iter([('WARD001',), ('WARD002',), ('WARD003',)])
        mock_execute.return_value = mock_result
        
        # Mock get_ward_code_for_candidate_type
        with patch('main.api_routes.get_ward_code_for_candidate_type') as mock_get_ward_code:
            mock_get_ward_code.return_value = 'ward_code'
            
            response = self.client.get('/api/v1/wards')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['candidate_type'] == 'ward'
            assert len(data['wards']) == 3
            assert data['count'] == 3
            assert data['wards'][0]['ward_id'] == 'WARD001'

    @patch('main.api_routes.get_ward_code_for_candidate_type')
    def test_get_available_wards_with_candidate_type(self, mock_get_ward_code):
        """Test retrieval with specific candidate type."""
        mock_get_ward_code.return_value = 'municipal_code'
        
        with patch('main.api_routes.db.session.execute') as mock_execute:
            mock_result = MagicMock()
            mock_result.__iter__ = lambda self: iter([('WARD001',), ('WARD002',)])
            mock_execute.return_value = mock_result
            
            response = self.client.get('/api/v1/wards?candidate_type=municipal')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['candidate_type'] == 'municipal'

    @patch('main.api_routes.get_ward_code_for_candidate_type')
    def test_get_available_wards_no_ward_code(self, mock_get_ward_code):
        """Test when ward code cannot be determined."""
        mock_get_ward_code.return_value = None
        
        response = self.client.get('/api/v1/wards')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        
        assert data['error'] == 'No ward data available'

    @patch('main.api_routes.db.session.execute')
    def test_get_available_wards_database_error(self, mock_execute):
        """Test handling of database errors."""
        mock_execute.side_effect = Exception("Database connection error")
        
        with patch('main.api_routes.get_ward_code_for_candidate_type') as mock_get_ward_code:
            mock_get_ward_code.return_value = 'ward_code'
            
            response = self.client.get('/api/v1/wards')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            
            assert data['error'] == 'Internal server error'


class TestWardCodeHelper:
    """Test cases for the ward code helper function."""
    
    def setup_method(self):
        """Set up test client."""
        self.app = app
        self.client = app.test_client()
        self.app.config['TESTING'] = True

    @patch('main.api_routes.db.session.execute')
    def test_get_ward_code_for_candidate_type_success(self, mock_execute):
        """Test successful retrieval of ward code."""
        from main.api_routes import get_ward_code_for_candidate_type
        
        # Mock database result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = ('ward', '{"ward_code,ward_name"}')
        mock_execute.return_value = mock_result
        
        ward_code = get_ward_code_for_candidate_type('ward')
        
        assert ward_code == 'ward_code'

    @patch('main.api_routes.db.session.execute')
    def test_get_ward_code_for_candidate_type_no_data(self, mock_execute):
        """Test when no data is found."""
        from main.api_routes import get_ward_code_for_candidate_type
        
        # Mock database result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_execute.return_value = mock_result
        
        ward_code = get_ward_code_for_candidate_type('ward')
        
        assert ward_code is None

    @patch('main.api_routes.db.session.execute')
    def test_get_ward_code_for_candidate_type_error(self, mock_execute):
        """Test error handling."""
        from main.api_routes import get_ward_code_for_candidate_type
        
        mock_execute.side_effect = Exception("Database error")
        
        ward_code = get_ward_code_for_candidate_type('ward')
        
        assert ward_code is None


if __name__ == '__main__':
    pytest.main([__file__])
