export type Event = {
    id: number;
    title: string;
    event_link: string;
    start_datetime: string;
    end_datetime: string;
    note: string | null;
    valid: boolean;
    color: string | null;
    organizer: string;
    market: string;
    industry: string;
    attending: string | null;
    created_at: string;
    updated_at: string;
};