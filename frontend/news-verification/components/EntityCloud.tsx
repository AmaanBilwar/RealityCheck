import { motion } from "framer-motion";
import React from "react";

interface NEREntity {
  name: string;
  sentiment: string | number; // "positive"/"negative" or numeric value
  type: string;
}

const EntityCloud: React.FC<{ entities: NEREntity[] }> = ({ entities }) => {
  // Group entities by type
  const entityTypes: { [key: string]: NEREntity[] } = {};
  entities?.forEach(entity => {
    if (!entityTypes[entity.type]) {
      entityTypes[entity.type] = [];
    }
    entityTypes[entity.type].push(entity);
  });

  if (!entities || entities.length === 0) {
    return <div className="text-center text-muted-foreground">No entities detected</div>;
  }

  // Function to determine sentiment color and intensity
  const getSentimentColor = (sentiment: string | number) => {
    if (typeof sentiment === 'number') {
      if (sentiment > 0) return `rgba(34, 197, 94, ${Math.min(Math.abs(sentiment), 1)})`;
      return `rgba(239, 68, 68, ${Math.min(Math.abs(sentiment), 1)})`;
    }
    if (sentiment?.toLowerCase().includes('positive')) return "rgb(34, 197, 94)";
    if (sentiment?.toLowerCase().includes('negative')) return "rgb(239, 68, 68)";
    return "rgb(148, 163, 184)";
  };

  return (
    <div className="space-y-6">
      {Object.keys(entityTypes).map(type => (
        <div key={type} className="mb-6">
          <h4 className="text-md font-semibold mb-3 capitalize">{type}s</h4>
          <div className="flex flex-wrap gap-2">
            {entityTypes[type].map((entity, idx) => (
              <motion.div
                key={`${entity.name}-${idx}`}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: idx * 0.05, type: "spring", stiffness: 200, damping: 15 }}
                whileHover={{ scale: 1.1, boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.1)" }}
                className="group relative cursor-pointer"
              >
                <div 
                  style={{ backgroundColor: getSentimentColor(entity.sentiment) }}
                  className={`
                    rounded-full px-3 py-1 text-sm font-medium
                    ${entity.sentiment?.toString().toLowerCase().includes('negative') ||
                      (typeof entity.sentiment === 'number' && entity.sentiment < 0) 
                      ? 'text-white' : 
                      entity.sentiment?.toString().toLowerCase().includes('positive') || 
                      (typeof entity.sentiment === 'number' && entity.sentiment > 0) 
                      ? 'text-white' : 'text-gray-800'}
                  `}
                >
                  {entity.name}
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    whileHover={{ opacity: 1, y: 0 }}
                    className="absolute left-1/2 -translate-x-1/2 top-full mt-2 z-10 invisible group-hover:visible"
                  >
                    <div className="bg-background shadow-lg rounded-md p-2 text-xs whitespace-nowrap">
                      <div><span className="font-bold">Sentiment:</span> {entity.sentiment}</div>
                    </div>
                  </motion.div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default EntityCloud;
