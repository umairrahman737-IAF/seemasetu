USE seemasetu;

ALTER TABLE issues
    MODIFY COLUMN asset_type ENUM(
        'Road', 'Bridge', 'Pothole', 'Streetlight', 'Water Supply',
        'Public Facility', 'Slope', 'Tunnel', 'Other'
    ) NOT NULL,
    ADD COLUMN urgency ENUM('Routine', 'Soon', 'Urgent', 'Immediate')
        NOT NULL DEFAULT 'Soon' AFTER severity;