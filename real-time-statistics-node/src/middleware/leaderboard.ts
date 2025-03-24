import { Request, Response, NextFunction } from 'express';
import { Redis as Dragonfly } from 'ioredis';
import { keyForCurrMonth } from '../utils/keyGenerator';

export const MONTHLY_LEADERBOARD_PREFIX = 'monthly_leaderboard';

// Middleware to add points to user's leaderboard score.
export const addLeaderboardPoints = (dragonfly: Dragonfly) => {
    return async (req: Request, res: Response, next: NextFunction) => {
        // Assume userId is passed in the request body
        const userId = req.body.userId;
        if (!userId) {
            return res.status(400).json({ error: 'userId is required' });
        }

        // Add 10 points for the user to the leaderboard key (Sorted Set) for the current month.
        // Of course, you can define different points for different user actions.
        const leaderboardKey = keyForCurrMonth(MONTHLY_LEADERBOARD_PREFIX)
        await dragonfly.zincrby(leaderboardKey, 10, userId);

        console.log(`Added 10 points for user ${userId} in ${leaderboardKey}`);
        next();
    };
};
