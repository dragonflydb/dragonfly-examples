import { Request, Response, NextFunction } from 'express';
import { Redis as Dragonfly } from 'ioredis';
import { keyForCurrMonth } from '../utils/currentMonth';

export const MONTHLY_ACTIVE_USER_PREFIX = 'monthly_active_users';

// Middleware to track user actions.
export const trackMonthlyActiveUser = (dragonfly: Dragonfly) => {
    return async (req: Request, res: Response, next: NextFunction) => {
        // Assume userId is passed in the request body.
        const userId = req.body.userId;
        if (!userId) {
            return res.status(400).json({ error: 'userId is required' });
        }

        // Add user to the active user key (HyperLogLog) for the current month.
        const key = keyForCurrMonth(MONTHLY_ACTIVE_USER_PREFIX);
        await dragonfly.pfadd(key, userId);

        console.log(`Tracked user ${userId} for ${key}`);
        next();
    };
};
