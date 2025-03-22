import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  FormControl, 
  FormLabel, 
  Input, 
  Textarea, 
  Select, 
  VStack, 
  Heading, 
  Text,
  useToast,
  Alert,
  AlertIcon,
  FormHelperText,
  Divider
} from '@chakra-ui/react';
import { useForm } from 'react-hook-form';
import axios from 'axios';

const CORRECTABLE_FIELDS = [
  { value: 'address', label: 'Address' },
  { value: 'city', label: 'City' },
  { value: 'state', label: 'State' },
  { value: 'zip_code', label: 'Zip Code' },
  { value: 'price', label: 'Price' },
  { value: 'bedrooms', label: 'Bedrooms' },
  { value: 'bathrooms', label: 'Bathrooms' },
  { value: 'square_feet', label: 'Square Feet' },
  { value: 'year_built', label: 'Year Built' },
  { value: 'property_type', label: 'Property Type' },
  { value: 'description', label: 'Description' }
];

const PropertyCorrectionForm = ({ propertyId, propertyName, onSuccess }) => {
  const { register, handleSubmit, formState: { errors, isSubmitting }, reset, watch } = useForm();
  const [selectedFields, setSelectedFields] = useState([]);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const toast = useToast();

  const onSubmit = async (data) => {
    try {
      // Format the data for the API
      const updatedValues = {};
      selectedFields.forEach(field => {
        updatedValues[field] = data[field];
      });

      const correctionData = {
        property_id: propertyId,
        corrected_fields: selectedFields,
        updated_values: updatedValues,
        submission_notes: data.notes,
        submitter_email: data.email,
        submitter_name: data.name
      };

      // Submit the correction
      await axios.post('/api/v1/corrections/', correctionData);
      
      // Show success message
      setSubmitSuccess(true);
      reset();
      setSelectedFields([]);
      
      toast({
        title: 'Correction submitted',
        description: 'Thank you for your contribution. Our team will review your correction.',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      console.error('Error submitting correction:', error);
      toast({
        title: 'Error submitting correction',
        description: error.response?.data?.detail || 'An unexpected error occurred',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleFieldSelect = (e) => {
    const value = e.target.value;
    if (value && !selectedFields.includes(value)) {
      setSelectedFields([...selectedFields, value]);
    }
  };

  const removeField = (field) => {
    setSelectedFields(selectedFields.filter(f => f !== field));
  };

  if (submitSuccess) {
    return (
      <Box p={5} borderWidth={1} borderRadius="md" shadow="md">
        <Alert status="success" mb={4}>
          <AlertIcon />
          Thank you for submitting a correction!
        </Alert>
        <Text mb={4}>
          Our team will review your correction and update the property listing if approved.
        </Text>
        <Button 
          colorScheme="blue" 
          onClick={() => setSubmitSuccess(false)}
        >
          Submit another correction
        </Button>
      </Box>
    );
  }

  return (
    <Box p={5} borderWidth={1} borderRadius="md" shadow="md">
      <Heading size="md" mb={4}>Submit a Correction for {propertyName}</Heading>
      <Text mb={4}>
        See something incorrect about this property listing? Submit a correction below, and our team will review it.
      </Text>

      <form onSubmit={handleSubmit(onSubmit)}>
        <VStack spacing={4} align="stretch">
          <FormControl>
            <FormLabel>Select field to correct</FormLabel>
            <Select 
              placeholder="Choose a field to correct" 
              onChange={handleFieldSelect}
              value=""
            >
              {CORRECTABLE_FIELDS.map(field => (
                <option 
                  key={field.value} 
                  value={field.value}
                  disabled={selectedFields.includes(field.value)}
                >
                  {field.label}
                </option>
              ))}
            </Select>
          </FormControl>

          {selectedFields.length > 0 && (
            <Box borderWidth={1} borderRadius="md" p={4} bg="gray.50">
              <Text fontWeight="bold" mb={2}>Fields to correct:</Text>
              <VStack spacing={4} align="stretch">
                {selectedFields.map(field => {
                  const fieldInfo = CORRECTABLE_FIELDS.find(f => f.value === field);
                  return (
                    <FormControl key={field} isRequired>
                      <FormLabel>{fieldInfo.label}</FormLabel>
                      <Box display="flex">
                        <Input
                          {...register(field, { required: true })}
                          mr={2}
                          placeholder={`Corrected ${fieldInfo.label}`}
                        />
                        <Button
                          colorScheme="red"
                          size="sm"
                          onClick={() => removeField(field)}
                        >
                          Remove
                        </Button>
                      </Box>
                    </FormControl>
                  );
                })}
              </VStack>
            </Box>
          )}

          <Divider />

          <FormControl isRequired>
            <FormLabel>Your Name</FormLabel>
            <Input 
              {...register('name', { required: 'Please provide your name' })} 
              placeholder="Your name"
            />
            {errors.name && (
              <FormHelperText color="red.500">{errors.name.message}</FormHelperText>
            )}
          </FormControl>

          <FormControl isRequired>
            <FormLabel>Your Email</FormLabel>
            <Input 
              {...register('email', { 
                required: 'Please provide your email',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Invalid email address'
                }
              })} 
              placeholder="Your email"
            />
            {errors.email && (
              <FormHelperText color="red.500">{errors.email.message}</FormHelperText>
            )}
          </FormControl>

          <FormControl>
            <FormLabel>Additional Notes (optional)</FormLabel>
            <Textarea 
              {...register('notes')} 
              placeholder="Any additional information that might be helpful"
              rows={4}
            />
          </FormControl>

          <Button 
            colorScheme="blue" 
            type="submit" 
            isLoading={isSubmitting}
            isDisabled={selectedFields.length === 0}
          >
            Submit Correction
          </Button>
        </VStack>
      </form>
    </Box>
  );
};

export default PropertyCorrectionForm; 