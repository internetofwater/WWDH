/**
 * Copyright 2025 Lincoln Institute of Land Policy
 * SPDX-License-Identifier: MIT
 */
'use client';

import { Box, Button, Collapse, Group, Paper } from '@mantine/core';
import styles from '@/features/Header/Header.module.css';
import { useDisclosure } from '@mantine/hooks';
import { Filters } from '@/features/Header/Filters';
import { Region } from '@/features/Header/Selectors/Region';
import { Reservoir } from '@/features/Header/Selectors/Reservoir';
import { Suspense } from 'react';
import dynamic from 'next/dynamic';
import Image from 'next/image';
import { Basin } from '@/features/Header/Selectors/Basin';
import { ClearAll } from '@/features/Header/Selectors/ClearAll';

const DarkModeToggle = dynamic(() => import('./DarkModeToggle'), {
    ssr: false,
});

/**

 * @component
 */
const Header: React.FC = () => {
    const [opened, { toggle }] = useDisclosure(false);

    return (
        <Box component="div" className={styles.topBarContainer}>
            <Paper radius={0} shadow="xs" className={styles.topBarPaper}>
                <Group justify="space-between" align="center">
                    <Group gap="xl">
                        <Box component="span" darkHidden>
                            <Image
                                src={'/BofR-logo-dark.png'}
                                alt="United States Bureau of Reclamation Logo"
                                width={157}
                                height={50}
                            />
                        </Box>
                        <Box component="span" lightHidden>
                            <Image
                                src={'/BofR-logo-white.png'}
                                alt="United States Bureau of Reclamation Logo"
                                width={157}
                                height={50}
                            />
                        </Box>
                        <Suspense>
                            <DarkModeToggle />
                        </Suspense>
                    </Group>
                    <Group gap="lg">
                        <Region />
                        <Basin />
                        {/* Group these so they move together when decreasing screen width */}
                        <Group>
                            <Reservoir />
                            <ClearAll />
                        </Group>
                    </Group>
                    <Button variant="default" onClick={toggle}>
                        Show Filters
                    </Button>
                </Group>
                <Collapse in={opened}>
                    <Filters />
                </Collapse>
            </Paper>
        </Box>
    );
};

export default Header;
