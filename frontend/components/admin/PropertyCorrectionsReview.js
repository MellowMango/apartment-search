import React, { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Button,
  Badge,
  Text,
  Flex,
  HStack,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Textarea,
  Select,
  FormControl,
  FormLabel,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
  VStack,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel
} from '@chakra-ui/react';
import axios from 'axios';
import { format } from 'date-fns';

const PropertyCorrectionsReview = () => {
  const [corrections, setCorrections] = useState([]);
  const [correction, setCorrection] = useState(null);
  const [status, setStatus] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewStatus, setReviewStatus] = useState('approved');
  const [pendingCount, setPendingCount] = useState(0);
  const [property, setProperty] = useState(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);
  const limit = 10;
  
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();

  useEffect(() => {
    fetchPendingCount();
    fetchCorrections();
  }, [status, page]);

  const fetchPendingCount = async () => {
    try {
      const { data } = await axios.get('/api/v1/corrections/pending-count');
      setPendingCount(data.count);
    } catch (error) {
      console.error('Error fetching pending count:', error);
    }
  };

  const fetchCorrections = async () => {
    setLoading(true);
    setError(null);
    try {
      let endpoint = `/api/v1/corrections/?skip=${page * limit}&limit=${limit}`;
      
      if (status !== 'all') {
        endpoint += `&status=${status}`;
      }
      
      const { data } = await axios.get(endpoint);
      setCorrections(data.items);
      setHasMore(data.has_more);
      setTotal(data.total);
    } catch (error) {
      console.error('Error fetching corrections:', error);
      setError('Failed to load property corrections. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const fetchPropertyDetails = async (propertyId) => {
    try {
      const { data } = await axios.get(`/api/v1/properties/${propertyId}`);
      setProperty(data);
    } catch (error) {
      console.error('Error fetching property details:', error);
      toast({
        title: 'Error',
        description: 'Failed to load property details',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleViewCorrection = async (correction) => {
    setCorrection(correction);
    setReviewNotes('');
    setReviewStatus('approved');
    await fetchPropertyDetails(correction.property_id);
    onOpen();
  };

  const handleReviewSubmit = async () => {
    try {
      await axios.post(`/api/v1/corrections/${correction.id}/review`, {
        status: reviewStatus,
        review_notes: reviewNotes
      });
      
      onClose();
      
      toast({
        title: 'Review submitted',
        description: `Correction was ${reviewStatus} successfully.`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      
      // Refresh the data
      fetchPendingCount();
      fetchCorrections();
    } catch (error) {
      console.error('Error submitting review:', error);
      toast({
        title: 'Error',
        description: 'Failed to submit review',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'pending':
        return <Badge colorScheme="yellow">Pending</Badge>;
      case 'approved':
        return <Badge colorScheme="green">Approved</Badge>;
      case 'rejected':
        return <Badge colorScheme="red">Rejected</Badge>;
      default:
        return <Badge>Unknown</Badge>;
    }
  };

  const renderChanges = (correction) => {
    if (!correction) return null;
    
    return (
      <Box mt={4}>
        <Heading size="sm" mb={2}>Changes</Heading>
        <Table size="sm" variant="simple">
          <Thead>
            <Tr>
              <Th>Field</Th>
              <Th>Original Value</Th>
              <Th>Updated Value</Th>
            </Tr>
          </Thead>
          <Tbody>
            {correction.corrected_fields.map(field => (
              <Tr key={field}>
                <Td fontWeight="bold">{field}</Td>
                <Td>{correction.original_values && correction.original_values[field] !== undefined 
                    ? String(correction.original_values[field]) 
                    : 'N/A'}</Td>
                <Td bg="green.50">{correction.updated_values && correction.updated_values[field] !== undefined 
                    ? String(correction.updated_values[field]) 
                    : 'N/A'}</Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      </Box>
    );
  };

  const renderPropertyDetails = () => {
    if (!property) return <Spinner />;
    
    return (
      <Box mt={4}>
        <Heading size="sm" mb={2}>Property Details</Heading>
        <Table size="sm" variant="simple">
          <Tbody>
            <Tr>
              <Td fontWeight="bold">ID</Td>
              <Td>{property.id}</Td>
            </Tr>
            <Tr>
              <Td fontWeight="bold">Name</Td>
              <Td>{property.property_name || 'N/A'}</Td>
            </Tr>
            <Tr>
              <Td fontWeight="bold">Address</Td>
              <Td>{property.address || 'N/A'}</Td>
            </Tr>
            <Tr>
              <Td fontWeight="bold">City</Td>
              <Td>{property.city || 'N/A'}</Td>
            </Tr>
            <Tr>
              <Td fontWeight="bold">State</Td>
              <Td>{property.state || 'N/A'}</Td>
            </Tr>
            <Tr>
              <Td fontWeight="bold">Zip Code</Td>
              <Td>{property.zip_code || 'N/A'}</Td>
            </Tr>
          </Tbody>
        </Table>
      </Box>
    );
  };

  return (
    <Box>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg">Property Corrections</Heading>
        <Badge colorScheme="yellow" fontSize="md" p={2}>
          {pendingCount} Pending
        </Badge>
      </Flex>
      
      <Flex mb={6} justify="space-between" align="center">
        <HStack>
          <Text>Filter by status:</Text>
          <Select 
            value={status} 
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(0);
            }}
            width="150px"
          >
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </Select>
        </HStack>
        
        <Text>
          Showing {corrections.length} of {total} corrections
        </Text>
      </Flex>
      
      {loading ? (
        <Flex justify="center" my={10}>
          <Spinner size="xl" />
        </Flex>
      ) : error ? (
        <Alert status="error">
          <AlertIcon />
          {error}
        </Alert>
      ) : corrections.length === 0 ? (
        <Alert status="info">
          <AlertIcon />
          No corrections found matching the current filter.
        </Alert>
      ) : (
        <>
          <Box overflowX="auto">
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th>ID</Th>
                  <Th>Property</Th>
                  <Th>Submitted By</Th>
                  <Th>Date Submitted</Th>
                  <Th>Status</Th>
                  <Th>Fields</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {corrections.map((correction) => (
                  <Tr key={correction.id}>
                    <Td>{correction.id}</Td>
                    <Td>ID: {correction.property_id}</Td>
                    <Td>
                      <Text>{correction.submitter_name}</Text>
                      <Text fontSize="sm" color="gray.600">{correction.submitter_email}</Text>
                    </Td>
                    <Td>{format(new Date(correction.submission_date), 'MMM d, yyyy')}</Td>
                    <Td>{getStatusBadge(correction.status)}</Td>
                    <Td>{correction.corrected_fields.join(', ')}</Td>
                    <Td>
                      <Button 
                        size="sm" 
                        colorScheme="blue"
                        onClick={() => handleViewCorrection(correction)}
                      >
                        View
                      </Button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
          
          <Flex justify="space-between" mt={6}>
            <Button 
              onClick={() => setPage(Math.max(0, page - 1))}
              isDisabled={page === 0}
            >
              Previous
            </Button>
            <Text>Page {page + 1}</Text>
            <Button 
              onClick={() => setPage(page + 1)}
              isDisabled={!hasMore}
            >
              Next
            </Button>
          </Flex>
        </>
      )}
      
      {/* Correction Detail Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            Review Correction #{correction?.id}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {correction && (
              <VStack spacing={4} align="stretch">
                <Box>
                  <Text fontWeight="bold">Submitted by:</Text>
                  <Text>{correction.submitter_name} ({correction.submitter_email})</Text>
                </Box>
                
                <Box>
                  <Text fontWeight="bold">Submission Date:</Text>
                  <Text>{format(new Date(correction.submission_date), 'MMM d, yyyy h:mm a')}</Text>
                </Box>
                
                {correction.submission_notes && (
                  <Box>
                    <Text fontWeight="bold">Submission Notes:</Text>
                    <Text>{correction.submission_notes}</Text>
                  </Box>
                )}
                
                <Tabs variant="enclosed">
                  <TabList>
                    <Tab>Changes</Tab>
                    <Tab>Property Details</Tab>
                  </TabList>
                  <TabPanels>
                    <TabPanel>
                      {renderChanges(correction)}
                    </TabPanel>
                    <TabPanel>
                      {renderPropertyDetails()}
                    </TabPanel>
                  </TabPanels>
                </Tabs>
                
                {correction.status === 'pending' && (
                  <>
                    <FormControl>
                      <FormLabel>Review Status</FormLabel>
                      <Select
                        value={reviewStatus}
                        onChange={(e) => setReviewStatus(e.target.value)}
                      >
                        <option value="approved">Approve</option>
                        <option value="rejected">Reject</option>
                      </Select>
                    </FormControl>
                    
                    <FormControl>
                      <FormLabel>Review Notes (optional)</FormLabel>
                      <Textarea
                        value={reviewNotes}
                        onChange={(e) => setReviewNotes(e.target.value)}
                        placeholder="Add notes about your decision..."
                      />
                    </FormControl>
                  </>
                )}
                
                {correction.status !== 'pending' && (
                  <Box>
                    <Text fontWeight="bold">Review Status:</Text>
                    <Text>{getStatusBadge(correction.status)}</Text>
                    
                    {correction.review_notes && (
                      <>
                        <Text fontWeight="bold" mt={2}>Review Notes:</Text>
                        <Text>{correction.review_notes}</Text>
                      </>
                    )}
                    
                    <Text fontWeight="bold" mt={2}>Reviewed On:</Text>
                    <Text>{correction.review_date ? format(new Date(correction.review_date), 'MMM d, yyyy h:mm a') : 'N/A'}</Text>
                  </Box>
                )}
              </VStack>
            )}
          </ModalBody>
          
          <ModalFooter>
            {correction?.status === 'pending' ? (
              <>
                <Button colorScheme="blue" mr={3} onClick={handleReviewSubmit}>
                  Submit Review
                </Button>
                <Button variant="ghost" onClick={onClose}>Cancel</Button>
              </>
            ) : (
              <Button variant="ghost" onClick={onClose}>Close</Button>
            )}
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default PropertyCorrectionsReview; 