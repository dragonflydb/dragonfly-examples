import {Redis as Dragonfly} from 'ioredis';
import {Value} from '@sinclair/typebox/value'

import {AdMetadata, UserAdPreferences} from './types';

export class AdMetadataStore {
    private client: Dragonfly;
    static readonly AD_PREFIX = 'ad';
    static readonly AD_METADATA_PREFIX = `${AdMetadataStore.AD_PREFIX}:metadata`;
    static readonly AD_CATEGORY_PREFIX = `${AdMetadataStore.AD_PREFIX}:category`;
    static readonly AD_USER_PREFERENCE_PREFIX = `${AdMetadataStore.AD_PREFIX}:user_preference`;
    static readonly SET_MEMBER_COUNT = 10;

    constructor(client: Dragonfly) {
        this.client = client;
    }

    metadataKey(metadataId: string): string {
        return `${AdMetadataStore.AD_METADATA_PREFIX}:${metadataId}`;
    }

    categoryKey(metadataCategory: string): string {
        return `${AdMetadataStore.AD_CATEGORY_PREFIX}:${metadataCategory}`;
    }

    userPreferenceKey(userId: string): string {
        return `${AdMetadataStore.AD_USER_PREFERENCE_PREFIX}:${userId}`;
    }

    async createAdMetadata(metadata: AdMetadata): Promise<void> {
        await this.client.hmset(this.metadataKey(metadata.id), metadata);
        await this.client.sadd(this.categoryKey(metadata.category), metadata.id);
    }

    async createUserPreference(userAdPreferences: UserAdPreferences): Promise<void> {
        await this.client.sadd(this.userPreferenceKey(userAdPreferences.userId), userAdPreferences.categories);
    }

    async getAdMetadataListByUserPreference(userId: string): Promise<Array<AdMetadata>> {
        const [_, categoryKeys] = await this.client.sscan(
            this.userPreferenceKey(userId),
            0,
            'COUNT',
            AdMetadataStore.SET_MEMBER_COUNT,
        );
        const pipeline = this.client.pipeline();
        categoryKeys.forEach((category: string) => {
            pipeline.sscan(
                this.categoryKey(category),
                0,
                'COUNT',
                AdMetadataStore.SET_MEMBER_COUNT,
            );
        });
        const results = await pipeline.exec();
        if (!results) {
            return [];
        }
        const adIds = results.map(([error, scanResult]) => {
            if (error) {
                throw error;
            }
            if (!scanResult) {
                return [];
            }
            // scanResult is a tuple of [string, Array<string>]
            // The 1st element is the cursor.
            // The 2nd element is the array of ids.
            const [_, ids] = scanResult as [string, Array<string>];
            return ids;
        }).flat();
        return await this.getAdMetadataList(adIds);
    }

    async getAdMetadataList(ids: Array<string>): Promise<Array<AdMetadata>> {
        const pipeline = this.client.pipeline();
        ids.forEach((id: string) => {
            pipeline.hgetall(this.metadataKey(id))
        });
        const results = await pipeline.exec();
        if (!results) {
            return [];
        }
        return results.map(([error, hash]) => {
            if (error) {
                throw error;
            }
            if (!hash) {
                return null;
            }
            if (!Value.Check(AdMetadata, hash)) {
                return null;
            }
            return hash;
        }).filter((hash) => hash !== null) as Array<AdMetadata>;
    }
}
