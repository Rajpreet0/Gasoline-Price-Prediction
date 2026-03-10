
export type Location = {
    latitude: number;
    longitude: number;
};

export type Station = {
    id: string;
    name: string;
    brand: string;
    street: string;
    place: string;
    lat: number;
    lng: number;
    dist: number;
    isOpen: boolean;
    e5: number | null;
    e10: number | null;
    diesel: number | null;
};