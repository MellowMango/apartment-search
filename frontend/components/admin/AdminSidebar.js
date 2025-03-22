import React from 'react';
import { Box, Flex, Stack, Icon, Text, Link, Divider } from '@chakra-ui/react';
import NextLink from 'next/link';
import { useRouter } from 'next/router';
import { 
  FaHome, 
  FaBuilding, 
  FaUsers, 
  FaUserTie, 
  FaCreditCard, 
  FaChartLine, 
  FaCog,
  FaMapMarkerAlt,
  FaClipboardCheck
} from 'react-icons/fa';

const NavItem = ({ icon, children, href, isActive }) => {
  return (
    <NextLink href={href} passHref>
      <Link 
        textDecoration="none" 
        _hover={{ textDecoration: 'none' }}
      >
        <Flex
          align="center"
          px="4"
          py="3"
          cursor="pointer"
          role="group"
          fontWeight={isActive ? "bold" : "normal"}
          bg={isActive ? "blue.50" : "transparent"}
          color={isActive ? "blue.600" : "gray.700"}
          borderRadius="md"
          _hover={{
            bg: 'blue.50',
            color: 'blue.600',
          }}
        >
          {icon && (
            <Icon
              mr="3"
              fontSize="16"
              as={icon}
              _groupHover={{
                color: 'blue.600',
              }}
            />
          )}
          <Text fontSize="sm">{children}</Text>
        </Flex>
      </Link>
    </NextLink>
  );
};

const AdminSidebar = () => {
  const router = useRouter();
  const currentPath = router.pathname;

  const navItems = [
    {
      label: 'Dashboard',
      icon: FaHome,
      href: '/admin',
    },
    {
      label: 'Properties',
      icon: FaBuilding,
      href: '/admin/properties',
    },
    {
      label: 'Users',
      icon: FaUsers,
      href: '/admin/users',
    },
    {
      label: 'Brokers',
      icon: FaUserTie,
      href: '/admin/brokers',
    },
    {
      label: 'Subscriptions',
      icon: FaCreditCard,
      href: '/admin/subscriptions',
    },
    {
      label: 'Analytics',
      icon: FaChartLine,
      href: '/admin/analytics',
    },
    {
      label: 'Geocoding',
      icon: FaMapMarkerAlt,
      href: '/admin/geocoding',
    },
    {
      label: 'Corrections',
      icon: FaClipboardCheck,
      href: '/admin/corrections',
    },
    {
      label: 'Settings',
      icon: FaCog,
      href: '/admin/settings',
    },
  ];

  return (
    <Box
      as="nav"
      pos="fixed"
      top="0"
      left="0"
      zIndex="sticky"
      h="full"
      overflowX="hidden"
      overflowY="auto"
      bg="white"
      borderRight="1px"
      borderRightColor="gray.200"
      w="60"
      px="4"
      py="6"
    >
      <Flex justify="center" mb="8">
        <Text fontSize="2xl" fontWeight="bold" color="blue.600">
          Admin Portal
        </Text>
      </Flex>
      <Stack spacing="0">
        {navItems.map((item) => (
          <NavItem
            key={item.label}
            icon={item.icon}
            href={item.href}
            isActive={currentPath === item.href}
          >
            {item.label}
          </NavItem>
        ))}
      </Stack>
      <Divider my="6" />
      <Box px="4" fontSize="sm">
        <Text color="gray.500">©2023 Acquire Properties</Text>
      </Box>
    </Box>
  );
};

export default AdminSidebar;
 