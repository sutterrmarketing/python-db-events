// Create a new object with only the updatable fields'use client';

import {
  Box,
  Flex,
  Field,
  Fieldset,
  Input,
  Textarea,
  Button,
  NativeSelect,
} from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import { toaster } from "@/components/ui/toaster";
import { Event } from '@/types/event';
import { PREDEFINED_COLORS } from '@/types/color';

function isDarkColor(color: string | null): boolean {
  if (!color) return false;
  const hex = color.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  const brightness = ((r * 299) + (g * 587) + (b * 114)) / 1000;
  return brightness < 128;
}

interface EventCardProps {
  event: Event;
  onEventUpdate: (updatedEvent: Event) => void;
  onEventDelete: (deletedEventId: number) => void;
}

const EventCard: React.FC<EventCardProps> = ({ event, onEventUpdate, onEventDelete }) => {
  const [formData, setFormData] = useState<Event>(event);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setFormData(event);
  }, [event]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleBooleanChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value === 'true',
    }));
  };

  const handleUpdate = async () => {
    setIsLoading(true);
    try {
      
      const response = await fetch(`/api/events`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update event');
      }

      const updated = await response.json();
      toaster.create({ title: "Event updated successfully", type: "success" });
      onEventUpdate(updated);
    } catch (error) {
      toaster.create({
        title: "Error updating event",
        description: error instanceof Error ? error.message : "Unexpected error occurred.",
        type: "error",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    try {
      const response = await fetch(`/api/delete?id=${formData.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete event');
      }

      toaster.create({ title: "Event deleted", type: "success" });
      onEventDelete(formData.id);
    } catch (error) {
      toaster.create({
        title: "Error deleting event",
        description: error instanceof Error ? error.message : "Unexpected error occurred.",
        type: "error",
      });
    }
  };

  return (
    <Box borderWidth="1px" borderRadius="lg" p={6} boxShadow="lg" bg="white">
      <form>
        <Fieldset.Root size="lg">
          <Fieldset.Legend>Event Details</Fieldset.Legend>
          <Fieldset.Content>
            <Field.Root>
              <Field.Label>Title</Field.Label>
              <Input name="title" value={formData.title ?? ''} onChange={handleChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Link</Field.Label>
              <Input name="event_link" value={formData.event_link ?? ''} onChange={handleChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Start Datetime</Field.Label>
              <Input type="datetime-local" name="start_datetime" value={formData.start_datetime ?? ''} onChange={handleChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>End Datetime</Field.Label>
              <Input type="datetime-local" name="end_datetime" value={formData.end_datetime ?? ''} onChange={handleChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Organizer</Field.Label>
              <Input name="organizer" value={formData.organizer ?? ''} onChange={handleChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Market</Field.Label>
              <Input name="market" value={formData.market ?? ''} onChange={handleChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Industry</Field.Label>
              <Input name="industry" value={formData.industry ?? ''} onChange={handleChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Attending</Field.Label>
              <Input name="attending" value={formData.attending ?? ''} onChange={handleChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Color (optional)</Field.Label>
              <NativeSelect.Root size="sm" width="auto">
                <NativeSelect.Field 
                  name="color"
                  value={formData.color || ''}
                  onChange={handleChange}
                  placeholder="Select color"
                  style={{
                    backgroundColor: formData.color || 'transparent',
                    color: formData.color ? (isDarkColor(formData.color) ? 'white' : 'black') : 'inherit'
                  }}
                >
                  {PREDEFINED_COLORS.map((color) => (
                    <option 
                      key={color.name} 
                      value={color.value || ''} 
                      style={{
                        backgroundColor: color.value || 'transparent',
                        color: color.value ? (isDarkColor(color.value) ? 'white' : 'black') : 'inherit'
                      }}
                    >
                      {color.name}
                    </option>
                  ))}
                </NativeSelect.Field>
                <NativeSelect.Indicator />
              </NativeSelect.Root>
            </Field.Root>

            <Field.Root>
              <Field.Label>Note</Field.Label>
              <Textarea name="note" value={formData.note ?? ''} onChange={handleChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Valid</Field.Label>
              <NativeSelect.Root>
                <NativeSelect.Field
                  name="valid"
                  value={formData.valid ? 'true' : 'false'}
                  onChange={handleBooleanChange}
                >
                  <option value="true">Valid</option>
                  <option value="false">Invalid</option>
                </NativeSelect.Field>
                <NativeSelect.Indicator />
              </NativeSelect.Root>
            </Field.Root>
          </Fieldset.Content>
        </Fieldset.Root>

        <Flex justifyContent="flex-end" mt={6} gap={3}>
          <Button variant="outline" onClick={handleDelete}>Delete</Button>
          <Button loading={isLoading} onClick={handleUpdate} colorScheme="blue">Update</Button>
        </Flex>
      </form>
    </Box>
  );
};

export default EventCard;
