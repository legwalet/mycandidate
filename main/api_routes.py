from flask import jsonify, request
from .database.models import db
from .decorators import get_candidates
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

def get_ward_code_for_candidate_type(candidate_type):
    """
    Get the ward code field name for a given candidate type.
    This function determines which field contains the ward information.
    """
    try:
        # Get the locator information for the candidate type
        distinct_types_query = """
            SELECT DISTINCT candidate_type, locator FROM candidates
            WHERE candidate_type = :candidate_type
            LIMIT 1
        """
        result = db.session.execute(distinct_types_query, {'candidate_type': candidate_type})
        row = result.fetchone()
        
        if row:
            locator_values = row[1].strip("{}").split(',')
            return locator_values[0]  # First field is typically the ward code
        return None
    except Exception as e:
        logger.error(f"Error getting ward code for candidate type {candidate_type}: {e}")
        return None

def get_candidates_by_ward_id(ward_id, candidate_type='ward'):
    """
    Retrieve all candidates for a specific ward.
    
    Args:
        ward_id (str): The ward identifier
        candidate_type (str): The type of candidates to retrieve (default: 'ward')
    
    Returns:
        list: List of candidate dictionaries
    """
    try:
        # Get the ward code field name
        ward_code = get_ward_code_for_candidate_type(candidate_type)
        
        if not ward_code:
            logger.error(f"No ward code found for candidate type: {candidate_type}")
            return []
        
        # Query candidates for the specific ward
        query = f"""
            SELECT * FROM candidates
            WHERE {ward_code} = :ward_id
            AND candidate_type = :candidate_type
            ORDER BY orderno, party, name
        """
        
        params = {'ward_id': ward_id, 'candidate_type': candidate_type}
        result = db.session.execute(query, params)
        
        # Convert to list of dictionaries
        candidates = []
        column_names = result.keys()
        for row in result:
            candidate_dict = dict(zip(column_names, row))
            candidates.append(candidate_dict)
        
        return candidates
        
    except Exception as e:
        logger.error(f"Error retrieving candidates for ward {ward_id}: {e}")
        return []

def register_api_routes(app):
    """
    Register API routes with the Flask app.
    """
    
    @app.route('/api/v1/wards/<ward_id>/candidates', methods=['GET'])
    def get_ward_candidates(ward_id):
        """
        Get all candidates standing for election in the specified ward.
        
        Parameters:
        - ward_id (str): The ward identifier
        
        Query Parameters:
        - candidate_type (str, optional): The type of candidates to retrieve (default: 'ward')
        
        Returns:
        - JSON array of candidate objects
        
        Sample Response:
        [
            {
                "id": "1",
                "name": "John Doe",
                "party": "Democratic Party",
                "orderno": "1",
                "ward_code": "WARD001",
                "candidate_type": "ward"
            }
        ]
        """
        try:
            # Get candidate_type from query parameters, default to 'ward'
            candidate_type = request.args.get('candidate_type', 'ward')
            
            # Validate ward_id
            if not ward_id or not ward_id.strip():
                return jsonify({
                    'error': 'Invalid ward_id',
                    'message': 'Ward ID cannot be empty'
                }), 400
            
            # Get candidates for the ward
            candidates = get_candidates_by_ward_id(ward_id, candidate_type)
            
            if not candidates:
                return jsonify({
                    'ward_id': ward_id,
                    'candidate_type': candidate_type,
                    'candidates': [],
                    'message': f'No candidates found for ward {ward_id}'
                }), 200
            
            # Return successful response
            return jsonify({
                'ward_id': ward_id,
                'candidate_type': candidate_type,
                'candidates': candidates,
                'count': len(candidates)
            }), 200
            
        except Exception as e:
            logger.error(f"Error in get_ward_candidates API: {e}")
            return jsonify({
                'error': 'Internal server error',
                'message': 'An error occurred while retrieving candidates'
            }), 500
    
    @app.route('/api/v1/wards', methods=['GET'])
    def get_available_wards():
        """
        Get list of available wards.
        
        Returns:
        - JSON array of ward objects with their identifiers
        """
        try:
            candidate_type = request.args.get('candidate_type', 'ward')
            
            # Get the ward code field name
            ward_code = get_ward_code_for_candidate_type(candidate_type)
            
            if not ward_code:
                return jsonify({
                    'error': 'No ward data available',
                    'message': f'No ward code found for candidate type: {candidate_type}'
                }), 404
            
            # Get distinct wards
            query = f"""
                SELECT DISTINCT {ward_code} as ward_id
                FROM candidates
                WHERE candidate_type = :candidate_type
                ORDER BY {ward_code}
            """
            
            result = db.session.execute(query, {'candidate_type': candidate_type})
            wards = [{'ward_id': row[0]} for row in result]
            
            return jsonify({
                'candidate_type': candidate_type,
                'wards': wards,
                'count': len(wards)
            }), 200
            
        except Exception as e:
            logger.error(f"Error in get_available_wards API: {e}")
            return jsonify({
                'error': 'Internal server error',
                'message': 'An error occurred while retrieving wards'
            }), 500
