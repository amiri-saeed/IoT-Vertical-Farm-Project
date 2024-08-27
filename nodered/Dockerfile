# Use the official Node-RED base image
FROM nodered/node-red:latest

# Install additional nodes (adjust as needed)
RUN npm install @5minds/node-red-dashboard-2-processcube-dynamic-table
RUN npm install @colinl/node-red-dashboard-2-ui-gauge-classic
RUN npm install @flowfuse/node-red-dashboard
RUN npm install json-db-node-red
RUN npm install node-red-contrib-loop
RUN npm install node-red-dashboard
RUN npm install node-red-node-ui-table

# Copy the flows file
COPY flows.json /usr/src/node-red/flows.json

# Copy the additional files (JS, CSS, SVG, etc.)
COPY "Node_RED_Flow_1_files/" /usr/src/node-red/Node-RED_Flow_1_files/

# Copy the custom HTML file
COPY "Node_RED_Flow_1.html" /usr/src/node-red/Node_RED_Flow_1.html

# Expose the Node-RED port
EXPOSE 1880

# Start Node-RED with the specified user directory
CMD ["npm", "start", "--", "--userDir", "/usr/src/node-red"]
