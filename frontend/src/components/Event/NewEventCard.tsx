'use client';

import React, { useState } from 'react';
import {
  Box,
  Flex,
  Field,
  Fieldset,
  Input,
  Textarea,
  NativeSelect,
  Button,
  InputGroup,
} from '@chakra-ui/react';
import { toaster } from "@/components/ui/toaster";
import type { Event } from '@/types/event';
import { PREDEFINED_COLORS } from '@/types/color';


interface NewEventCardProps { 
  onEventAdd: () => void;
}

const NewEventCard: React.FC<NewEventCardProps> = ({ onEventAdd }) => {

    const getTodayDate = () => {
        const today = new Date();
        return today.toISOString().split('T')[0];
    };
  
    const [formData, setFormData] = useState<Omit<Event, "id" | "created_at" | "updated_at">>({
        title: '',
        event_link: '',
        start_datetime: '',
        end_datetime: '',
        valid: true,
        color: PREDEFINED_COLORS[0].value,
        note: '',
        organizer: '',
        market: '',
        industry: '',
        attending: '',
    });
    
    const [isLoading, setIsLoading] = useState(false);

    const handleInputChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
    ) => {
        const { name, value } = e.target;
        setFormData(prev => ({
        ...prev,
        [name]: name === 'color' && value === '' ? null : value
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (
            formData.title &&
            formData.event_link &&
            formData.start_datetime &&
            formData.end_datetime &&
            formData.organizer &&
            formData.market &&
            formData.industry
        ) {
            setIsLoading(true);
            try {
                const response = await fetch('/api/events/new', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to add event');
                }

                const data = await response.json();

                toaster.create({
                    title: "Event added successfully",
                    type: "success",
                });

                setFormData({
                    title: '',
                    event_link: '',
                    start_datetime: '',
                    end_datetime: '',
                    valid: true,
                    color: '',
                    note: '',
                    organizer: '',
                    market: '',
                    industry: '',
                    attending: '',
                });
              
                onEventAdd();
                
            } catch (error) {
                toaster.create({
                    title: "Error adding event",
                    description: error instanceof Error ? error.message : "An unexpected error occurred. Please try again.",
                    type: "error",
                });
            } finally { 
                setIsLoading(false);
            }
        } else {
            toaster.create({
                title: "Error adding event",
                description: "Please fill in all required fields",
                type: "error",
            });
        }
    };

  return (
    <Box borderWidth="1px" borderRadius="lg" p={6} boxShadow="lg" bg="white">
      <form onSubmit={handleSubmit}>
        <Fieldset.Root size="lg">
          <Fieldset.Legend>Event Details</Fieldset.Legend>
          <Fieldset.Content>
            <Field.Root>
              <Field.Label>Title</Field.Label>
              <Input name="title" value={formData.title} onChange={handleInputChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Link</Field.Label>
              <Input name="event_link" value={formData.event_link} onChange={handleInputChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Start Date/Time</Field.Label>
              <Input name="start_datetime" type="datetime-local" value={formData.start_datetime} onChange={handleInputChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>End Date/Time</Field.Label>
              <Input name="end_datetime" type="datetime-local" value={formData.end_datetime} onChange={handleInputChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Organizer</Field.Label>
              <Input name="organizer" value={formData.organizer} onChange={handleInputChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Market</Field.Label>
              <Input name="market" value={formData.market} onChange={handleInputChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Industry</Field.Label>
              <Input name="industry" value={formData.industry} onChange={handleInputChange} />
            </Field.Root>

            <Field.Root>
              <Field.Label>Attending (optional)</Field.Label>
              <Input 
                name="attending" 
                value={formData.attending || ''} 
                onChange={handleInputChange} 
                placeholder="Enter attending information"
              />
            </Field.Root>

            <Field.Root>
              <Field.Label>Color (optional)</Field.Label>
              <NativeSelect.Root size="sm" width="auto">
                <NativeSelect.Field 
                  name="color"
                  value={formData.color || ''}
                  onChange={handleInputChange}
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
              <Field.Label>Notes (optional)</Field.Label>
              <Textarea
                name="note"
                value={formData.note || ''}
                onChange={handleInputChange}
                placeholder="Enter any additional notes"
              />
            </Field.Root>
          </Fieldset.Content>
        </Fieldset.Root>

        <Flex justifyContent="flex-end" mt={4}>
             <Button 
                loading={isLoading} 
                onClick={handleSubmit}
                type="submit"
            >
                Add Event
            </Button>
        </Flex>

      </form>
    </Box>
  );
};

function isDarkColor(color: string | null): boolean {
  if (!color) return false;
  const hex = color.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);
  const brightness = ((r * 299) + (g * 587) + (b * 114)) / 1000;
  return brightness < 128;
}

export default NewEventCard;
