/**
 * Copyright 2025 Lincoln Institute of Land Policy
 * SPDX-License-Identifier: MIT
 */

import { useEffect, useRef, useState } from 'react';
import edrService from '@/services/init/edr.init';
import { Feature, FeatureCollection, Point } from 'geojson';
import { ReservoirProperties } from '@/features/Map/types';
import useMainStore, { ReservoirCollections } from '@/lib/main';
import { ReservoirConfigs } from '@/features/Map/consts';

export const useReservoirData = () => {
    const reservoirCollections = useMainStore(
        (state) => state.reservoirCollections
    );
    const setReservoirCollections = useMainStore(
        (state) => state.setReservoirCollections
    );

    const [loading, setLoading] = useState(false);
    const controller = useRef<AbortController | null>(null);
    const isMounted = useRef(true);

    const fetchReservoirLocations = async () => {
        try {
            setLoading(true);
            controller.current = new AbortController();
            const reservoirCollections: ReservoirCollections = {};

            for (const config of ReservoirConfigs) {
                const result = await edrService.getLocations<
                    FeatureCollection<Point, ReservoirProperties>
                >(config.id, {
                    signal: controller.current.signal,
                    params: {
                        'parameter-name': 'reservoirStorage',
                    },
                });
                reservoirCollections[config.id] = result;
            }

            if (isMounted.current) {
                setReservoirCollections(reservoirCollections);
                setLoading(false);
            }
        } catch (error) {
            if ((error as Error)?.name !== 'AbortError') {
                console.error(error);
                setLoading(false);
            }
        }
    };

    const fetchReservoirItem = async (
        reservoirId: string
    ): Promise<Feature<Point, ReservoirProperties> | null> => {
        try {
            controller.current = new AbortController();

            const feature = await edrService.getItem<
                Feature<Point, ReservoirProperties>
            >('rise-edr', reservoirId, {
                signal: controller.current.signal,
            });

            return feature;
        } catch (error) {
            if ((error as Error)?.name !== 'AbortError') {
                console.error(error);
            }
            return null;
        }
    };

    useEffect(() => {
        isMounted.current = true;
        if (!reservoirCollections) {
            void fetchReservoirLocations();
        }

        return () => {
            isMounted.current = false;
            controller.current?.abort();
        };
    }, []);

    return {
        reservoirCollections,
        loading,
        fetchReservoirItem,
    };
};
