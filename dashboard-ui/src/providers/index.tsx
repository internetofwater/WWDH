/**
 * Copyright 2025 Lincoln Institute of Land Policy
 * SPDX-License-Identifier: MIT
 */

'use client';

import { PropsWithChildren } from 'react';
import { Map as MapProvider } from '@/providers/Map';
import { Mantine as MantineProvider } from '@/providers/Mantine';

/**
 * Wrapping component for grouping all providers
 *
 * Providers:
 * - Mantine: Define theme for application
 * - Map: Allow access to map objects across application via hook useMap
 *
 * @component
 */
export const Providers: React.FC<PropsWithChildren> = ({ children }) => {
    return (
        <MantineProvider>
            <MapProvider>{children}</MapProvider>
        </MantineProvider>
    );
};
