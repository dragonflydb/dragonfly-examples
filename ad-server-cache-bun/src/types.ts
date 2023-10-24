import {Type, Static} from '@sinclair/typebox'

export const AdMetadata = Type.Object({
    id: Type.String(),
    title: Type.String(),
    category: Type.String(),
    clickURL: Type.String(),
    imageURL: Type.String(),
});

export type AdMetadata = Static<typeof AdMetadata>;

export const UserAdPreferences = Type.Object({
    userId: Type.String(),
    categories: Type.Array(Type.String()),
});

export type UserAdPreferences = Static<typeof UserAdPreferences>;
