'use client';

import { Flex, Link as ChakraLink, HStack, Box } from '@chakra-ui/react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { label: 'Dashboard', href: '/' },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <Box bg="gray.100" color="white" px={6} py={4} shadow="sm">
      <Flex align="center" justify="space-between">
        <HStack gap={8}>
          {navItems.map(({ label, href }) => (
            <ChakraLink
              as={Link}
              key={href}
              href={href}
              fontWeight={pathname === href ? 'bold' : 'normal'}
              _hover={{ textDecoration: 'underline' }}
            >
              {label}
            </ChakraLink>
          ))}
        </HStack>
      </Flex>
    </Box>
  );
}