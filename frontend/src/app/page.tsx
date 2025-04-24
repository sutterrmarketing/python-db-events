'use client';

import { useRef, useState, useCallback } from 'react';
import EventEditTable, { TableHeader, EventTableRef } from "@/components/Event/EventEditTable";
import { Button, Container, Box, Heading, VStack, HStack, CloseButton, Text } from "@chakra-ui/react";
import { LuCirclePlus, LuRefreshCw } from 'react-icons/lu';
import { toaster } from '@/components/ui/toaster';
import { Separator, Dialog, Portal, NativeSelect, Select } from '@chakra-ui/react';
import EventCard from '@/components/Event/EventCard';
import InputWithKbd from '@/components/InputWithKbd';
import { Event } from '@/types/event';
import NewEventCard from '@/components/Event/NewEventCard';
import { Sites } from '@/types/site';
import { Market } from '@/types/market';
import { Industry } from '@/types/industry';
import { Organizer } from '@/types/organizer';

type EventTimeFilterType = "all-events" | "upcoming-events" | "past-events";

export default function DashboardPage() {
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const eventTableRef = useRef<EventTableRef>(null);
  const [sortBy, setSortBy] = useState('start_datetime');
  const [sortOrder, setSortOrder] = useState('asc');
  const [selectedMarket, setSelectedMarket] = useState('all');
  const [selectedIndustry, setSelectedIndustry] = useState('all');
  const [selectedOrganizer, setSelectedOrganizer] = useState('all');
  const [eventTimeFilter, setEventTimeFilter] = useState<EventTimeFilterType>('all-events');

  const [isRefreshing, setIsRefreshing] = useState<boolean | string>(false);
  const [refreshedSites, setRefreshedSites] = useState<string[]>([]);
  const [selectedSiteToRefresh, setSelectedSiteToRefresh] = useState('all');

  const handleSearch = (term: string) => {
    eventTableRef.current?.setSearchTerm(term);
  };

  const handleEventUpdate = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  const handleEventAdd = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  const handleEventDelete = useCallback(() => {
    setSelectedEvent(null);
    setRefreshTrigger(prev => prev + 1);
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setRefreshedSites([]);

    const sitesToRefresh = selectedSiteToRefresh === 'all' ? Sites : [selectedSiteToRefresh];

    for (let i = 0; i < sitesToRefresh.length; i++) {
      const site = sitesToRefresh[i];
      setIsRefreshing(site);

      try {
        const res = await fetch('/api/events', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ websites: [site] }),
        });

        if (!res.ok) {
          const err = await res.json();
          toaster.create({ title: `Failed on ${site}`, description: err.detail || 'Unexpected server error', type: 'error' });
          break;
        }

        setRefreshTrigger(prev => prev + 1);
        setRefreshedSites(prev => [...prev, site]);
      } catch (error) {
        toaster.create({ title: `Network error on ${site}`, description: error instanceof Error ? error.message : "Unknown error", type: 'error' });
        break;
      }
    }

    setIsRefreshing(false);
  };

  const handleSelectEvent = (event: Event | null) => {
    setSelectedEvent(event);
    setSelectedEventId(event?.id || null);
  };

  return (
    <Container maxW="100%" py={8} px={4}>
      <HStack justifyContent="space-between" mb={6}>
        <Heading size="lg">Events Dashboard</Heading>
        <Box>
            <HStack justifyContent="space-between" alignItems="flex-start">
                {/* Refresh Control */}
                <HStack gap={4}>
                <NativeSelect.Root size="sm" width="auto">
                    <NativeSelect.Field
                    value={selectedSiteToRefresh}
                    onChange={(e) => setSelectedSiteToRefresh(e.target.value)}
                    >
                    <option value="all">All Sites</option>
                    {Sites.map(site => (
                        <option key={site} value={site}>{site}</option>
                    ))}
                    </NativeSelect.Field>
                    <NativeSelect.Indicator />
                </NativeSelect.Root>

                <Button
                    colorScheme="blue"
                    onClick={handleRefresh}
                    disabled={isRefreshing !== false}
                    loading={isRefreshing !== false}
                    loadingText={typeof isRefreshing === 'string' ? `Refreshing ${isRefreshing}` : 'Refreshing'}
                >
                    <LuRefreshCw />
                    {isRefreshing ? `Refreshing ${isRefreshing}` : 'Refresh'}
                </Button>
                </HStack>

                {/* Refreshed Sites Summary */}
                <Box
                maxHeight="100px"
                minWidth="250px"
                overflowY="auto"
                p={2}
                border="1px solid"
                borderColor="gray.200"
                borderRadius="md"
                fontSize="sm"
                color="gray.700"
                background="gray.50"
                >
                {refreshedSites.length > 0 ? (
                    <VStack align="start" gap={1}>
                    {refreshedSites.map(site => (
                        <Box key={site}>✅ {site}</Box>
                    ))}
                    </VStack>
                ) : (
                    <Text>No sites refreshed yet</Text>
                )}
                </Box>
            </HStack>
        </Box>

      </HStack>

      <VStack gapY={6} align="stretch">
        <Box borderWidth="2px" borderRadius="md" p={4} w="full" minWidth="1400px">
          <Heading size="md" mb={4}>Events List</Heading>

          <HStack mb={4}>
            <InputWithKbd onSearch={handleSearch} />
            <Dialog.Root>
              <Dialog.Trigger asChild>
                <Button colorScheme="gray" mr={3}><LuCirclePlus /> New Event</Button>
              </Dialog.Trigger>
              <Portal>
                <Dialog.Backdrop />
                <Dialog.Positioner>
                  <Dialog.Content maxWidth="500px">
                    <Dialog.Header>
                      <Dialog.Title>Add New Event</Dialog.Title>
                      <Dialog.CloseTrigger asChild>
                        <CloseButton size="sm" />
                      </Dialog.CloseTrigger>
                    </Dialog.Header>
                    <Dialog.Body p={3}>
                      <NewEventCard onEventAdd={handleEventAdd} />
                    </Dialog.Body>
                  </Dialog.Content>
                </Dialog.Positioner>
              </Portal>
            </Dialog.Root>
          </HStack>

          <HStack gap={4} align="flex-end" mb={4}>
            <Box>
              <Text fontSize="sm" mb={1}>Sort by</Text>
              <NativeSelect.Root size="sm" width="auto">
                <NativeSelect.Field 
                  value={sortBy} 
                  onChange={(e) => {
                    setSortBy(e.target.value);
                    setRefreshTrigger(prev => prev + 1);
                  }}
                >
                  <option value="start_datetime">Start Date/Time</option>
                  <option value="end_datetime">End Date/Time</option>
                  <option value="organizer">Organizer</option>
                  <option value="title">Title</option>
                  <option value="industry">Industry</option>
                  <option value="market">Market</option>
                  <option value="attending">Attending</option>
                  <option value="color">Color</option>
                </NativeSelect.Field>
                <NativeSelect.Indicator />
              </NativeSelect.Root>
            </Box>

            <Box>
              <Text fontSize="sm" mb={1}>Order</Text>
              <NativeSelect.Root size="sm" width="auto">
                <NativeSelect.Field 
                  value={sortOrder} 
                  onChange={(e) => {
                    setSortOrder(e.target.value);
                    setRefreshTrigger(prev => prev + 1);
                  }}
                >
                  <option value="asc">Ascending</option>
                  <option value="desc">Descending</option>
                </NativeSelect.Field>
                <NativeSelect.Indicator />
              </NativeSelect.Root>
            </Box>

            <Box>
              <Text fontSize="sm" mb={1}>Market</Text>
                <NativeSelect.Root size="sm" width="auto">
                  <NativeSelect.Field 
                    value={selectedMarket} 
                    onChange={(e) => {
                      setSelectedMarket(e.target.value);
                      setRefreshTrigger(prev => prev + 1);
                    }}
                  >
                    <option value="all">All Markets</option>
                    {Market.map(m => (
                      <option key={m} value={m}>{m}</option>
                    ))}
                  </NativeSelect.Field>
                  <NativeSelect.Indicator />
                </NativeSelect.Root>
            </Box>

            <Box>
              <Text fontSize="sm" mb={1}>Industry</Text>
              <NativeSelect.Root size="sm" width="auto">
                <NativeSelect.Field 
                  value={selectedIndustry} 
                  onChange={(e) => {
                    setSelectedIndustry(e.target.value);
                    setRefreshTrigger(prev => prev + 1);
                  }}
                >
                  <option value="all">All Industries</option>
                  {Industry.map(i => (
                    <option key={i} value={i}>{i}</option>
                  ))}
                </NativeSelect.Field>
                <NativeSelect.Indicator />
              </NativeSelect.Root>
            </Box>

            <Box>
              <Text fontSize="sm" mb={1}>Organizer</Text>
              <NativeSelect.Root size="sm" width="auto">
                <NativeSelect.Field 
                  value={selectedOrganizer} 
                  onChange={(e) => {
                    setSelectedOrganizer(e.target.value);
                    setRefreshTrigger(prev => prev + 1);
                  }}
                >
                  <option value="all">All Organizers</option>
                  {Organizer.map(o => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </NativeSelect.Field>
                <NativeSelect.Indicator />
              </NativeSelect.Root>
            </Box>

            <Box>
              <Text fontSize="sm" mb={1}>Event Time</Text>
              <NativeSelect.Root size="sm" width="auto">
                <NativeSelect.Field 
                  value={eventTimeFilter} 
                  onChange={(e) => setEventTimeFilter(e.target.value as EventTimeFilterType)}
                >
                  <option value="all-events">All Events</option>
                  <option value="upcoming-events">Upcoming Events</option>
                  <option value="past-events">Past Events</option>
                </NativeSelect.Field>
                <NativeSelect.Indicator />
              </NativeSelect.Root>
            </Box>

          </HStack>

          <Separator my={2} mx={4} />

          <Box borderWidth="2px" borderRadius="md" w="full" minWidth="1400px">
            <Box overflowX="auto" minWidth="1400px">
              <TableHeader />
            </Box>
            <Box maxH={600} overflowY="auto" minWidth="1400px">
              <EventEditTable
                ref={eventTableRef}
                onSelectEvent={handleSelectEvent}
                refreshTrigger={refreshTrigger}
                showHeader={false}
                selectedEventId={selectedEventId}
                sortBy={sortBy}
                sortOrder={sortOrder}
                selectedMarket={selectedMarket}
                selectedIndustry={selectedIndustry}
                selectedOrganizer={selectedOrganizer}
                eventTimeFilter={eventTimeFilter}
              />
            </Box>
          </Box>
        </Box>

        <Box borderWidth="2px" borderRadius="md" p={4} w="full">
          <Heading size="md" mb={3}>Selected Event</Heading>
          {selectedEvent ? (
            <EventCard
              event={selectedEvent}
              onEventUpdate={handleEventUpdate}
              onEventDelete={handleEventDelete}
            />
          ) : (
            <p>Select an event to view details.</p>
          )}
        </Box>
      </VStack>
    </Container>
  );
}
