"""
Prediction Model
"""
from datetime import datetime

from ..extensions import db


class Prediction(db.Model):
    """Prediction record model"""
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)  # Renamed file (CLASS_TIMESTAMP_USERNAME.ext)
    original_filename = db.Column(db.String(255), nullable=False)  # Original upload filename
    result_class = db.Column(db.String(50), nullable=False, index=True)  # 'Normal' or 'Down Syndrome'
    confidence = db.Column(db.Float, nullable=False)  # Prediction confidence (0-1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<Prediction {self.id} - {self.result_class} ({self.confidence:.2%})>'
    
    @property
    def confidence_percentage(self):
        """Return confidence as percentage string"""
        return f'{self.confidence * 100:.2f}%'
    
    @property
    def formatted_timestamp(self):
        """Return formatted timestamp"""
        return self.created_at.strftime('%d/%m/%Y %H:%M:%S')
