import React, { useState } from 'react';
import { ColumnMapping } from '../types/files';
import './ColumnMapper.css';

interface ColumnMapperProps {
  sourceColumns: string[];
  targetSchema: string[];
  mappings: { [key: string]: ColumnMapping };
  onUpdateMapping: (sourceColumn: string, targetColumn: string | null) => void;
}

const ColumnMapper: React.FC<ColumnMapperProps> = ({
  sourceColumns,
  targetSchema,
  mappings,
  onUpdateMapping,
}) => {
  const [selectedSource, setSelectedSource] = useState<string | null>(null);

  const isColumnMapped = (sourceColumn: string) => {
    return mappings[sourceColumn]?.target_column !== null;
  };

  const getTargetForSource = (sourceColumn: string) => {
    return mappings[sourceColumn]?.target_column;
  };

  const isTargetMapped = (targetColumn: string) => {
    return Object.values(mappings).some(
      mapping => mapping.target_column === targetColumn
    );
  };

  const handleSourceClick = (column: string) => {
    setSelectedSource(column);
  };

  const handleTargetClick = (targetColumn: string) => {
    if (selectedSource) {
      onUpdateMapping(selectedSource, targetColumn);
      setSelectedSource(null);
    }
  };

  return (
    <div className="column-mapper">
      <div className="source-columns">
        <h3>Source Columns</h3>
        {sourceColumns.map((column) => (
          <div
            key={column}
            className={`column-item ${selectedSource === column ? 'selected' : ''} ${
              isColumnMapped(column) ? 'mapped' : ''
            }`}
            onClick={() => handleSourceClick(column)}
          >
            <span className="column-name">{column}</span>
            {isColumnMapped(column) && (
              <span className="mapping-indicator">
                → {getTargetForSource(column)}
              </span>
            )}
          </div>
        ))}
      </div>

      <div className="target-columns">
        <h3>Target Schema</h3>
        {targetSchema.map((column) => (
          <div
            key={column}
            className={`column-item ${isTargetMapped(column) ? 'mapped' : 'available'}`}
            onClick={() => handleTargetClick(column)}
          >
            <span className="column-name">{column}</span>
            {isTargetMapped(column) && (
              <span className="mapping-indicator">✓</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ColumnMapper; 