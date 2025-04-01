import PropertyCorrectionForm from '../../components/PropertyCorrectionForm';
import { Box, Tabs, TabList, TabPanels, Tab, TabPanel, Heading, Divider } from '@chakra-ui/react';

const PropertyDetail = ({ property }) => {
  return (
    <Layout>
      <Box mt={10} mb={10}>
        <Divider mb={6} />
        
        <Tabs variant="enclosed">
          <TabList>
            <Tab>Property Details</Tab>
            <Tab>Map</Tab>
            <Tab>Submit Correction</Tab>
          </TabList>
          
          <TabPanels>
            <TabPanel>
              <PropertyDetails property={property} />
            </TabPanel>
            
            <TabPanel>
              <PropertyMap property={property} />
            </TabPanel>
            
            <TabPanel>
              <Box py={4}>
                <PropertyCorrectionForm 
                  propertyId={property.id} 
                  propertyName={property.property_name || `Property #${property.id}`}
                />
              </Box>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </Box>
    </Layout>
  );
};

const PropertyDetails = ({ property }) => {
  return (
    <Box>
      <Heading size="md" mb={3}>Description</Heading>
      <Text mb={6}>{property.description || "No description available."}</Text>
      
      <Heading size="md" mb={3}>Features</Heading>
      <SimpleGrid columns={[2, null, 3]} spacing={4} mb={6}>
        <Feature icon={FaBed} value={`${property.bedrooms || 'N/A'} Bedrooms`} />
        <Feature icon={FaBath} value={`${property.bathrooms || 'N/A'} Bathrooms`} />
        <Feature icon={FaRuler} value={`${property.square_feet ? `${property.square_feet.toLocaleString()} sq ft` : 'N/A'}`} />
        <Feature icon={FaCalendarAlt} value={`Built ${property.year_built || 'N/A'}`} />
        <Feature icon={FaHome} value={property.property_type || "N/A"} />
        <Feature icon={FaWarehouse} value={property.lot_size ? `${property.lot_size.toLocaleString()} sq ft lot` : 'N/A'} />
      </SimpleGrid>
      
      <SimpleGrid columns={[1, null, 2]} spacing={6}>
        <Box>
          <Heading size="md" mb={3}>Property Information</Heading>
          <VStack align="start" spacing={2}>
            <DetailItem label="MLS Number" value={property.mls_number || "N/A"} />
            <DetailItem label="Status" value={property.status || "N/A"} />
            <DetailItem label="Listed On" value={property.list_date ? new Date(property.list_date).toLocaleDateString() : "N/A"} />
            <DetailItem label="Property Tax" value={property.property_tax ? `$${property.property_tax.toLocaleString()}` : "N/A"} />
          </VStack>
        </Box>
        
        <Box>
          <Heading size="md" mb={3}>Location</Heading>
          <VStack align="start" spacing={2}>
            <DetailItem label="Address" value={property.address || "N/A"} />
            <DetailItem label="City" value={property.city || "N/A"} />
            <DetailItem label="State" value={property.state || "N/A"} />
            <DetailItem label="Zip Code" value={property.zip_code || "N/A"} />
            <DetailItem label="County" value={property.county || "N/A"} />
          </VStack>
        </Box>
      </SimpleGrid>
    </Box>
  );
};

const PropertyMap = ({ property }) => {
  if (!property.latitude || !property.longitude) {
    return <Box>Location information not available for this property.</Box>;
  }
  
  return (
    <Box height="400px" width="100%">
      <Map
        center={[property.latitude, property.longitude]}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <Marker position={[property.latitude, property.longitude]}>
          <Popup>
            {property.property_name || property.address}
          </Popup>
        </Marker>
      </Map>
    </Box>
  );
}; 