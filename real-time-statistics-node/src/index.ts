import express from 'express'
import dragonfly from './utils/dragonflyClient'
import { keyForCurrMonth, keyForMonth } from './utils/keyGenerator'
import { MONTHLY_ACTIVE_USER_PREFIX, trackMonthlyActiveUsers } from './middleware/activeUser'
import { MONTHLY_LEADERBOARD_PREFIX, addLeaderboardPoints } from './middleware/leaderboard'

// The Express application.
const app = express()
app.use(express.json())

// Dummy endpoint to simulate user actions.
// For the current month:
//  - Track this user as an active user.
//  - Add points for the user in the leaderboard.
app.post('/user-action', trackMonthlyActiveUsers(dragonfly), addLeaderboardPoints(dragonfly), (req, res) => {
	res.json({ message: 'User action finished successfully!' })
})

// Endpoint to get current monthly active users count.
app.get('/active-users-current-month', async (req, res) => {
	const key = keyForCurrMonth(MONTHLY_ACTIVE_USER_PREFIX)
	const count = await dragonfly.pfcount(key)
	res.json({ count })
})

// Endpoint to get active users count for the current and past month as a single value.
app.get('/active-users-past-two-months', async (req, res) => {
	const now = new Date()
	const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1)

    // Construct the HyperLogLog keys for the current and last months.
	const currMonthKey = keyForCurrMonth(MONTHLY_ACTIVE_USER_PREFIX)
	const lastMonthKey = keyForMonth(MONTHLY_ACTIVE_USER_PREFIX, lastMonth)

    // Calculate the last second of the current month in Unix timestamp.
    // The merge key should expire at that time to allow a new round of "past two months."
    const lastDayOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    lastDayOfMonth.setHours(23, 59, 59, 999);
    const expireAt = Math.floor(lastDayOfMonth.getTime() / 1000)

	// PFMERGE destkey [sourcekey [sourcekey ...]]
	//
	// The PFMERGE command merges the cardinalities from two (or more) source HyperLogLog keys.
	// The merged cardinality value is set to the destination key.
	// If the destination key exists, it is treated as one of the sources, and its cardinality will be included.
    // This design is intended, since HyperLogLog counts a unique value only once.
	//
	// The following code pipelines 3 commands: PFMERGE, PFCOUNT, and EXPIREAT.
	// The result of PFCOUNT is returned as the value.
	const mergeKey = 'active_users_past_two_months'
	const result = (await dragonfly
		.pipeline()
		.pfmerge(mergeKey, currMonthKey, lastMonthKey)
		.pfcount(mergeKey)
		.expireat(mergeKey, expireAt)
		.exec()) as [error: Error | null, result: unknown][]

	const [, [, count]] = result
	res.json({ count })
})

// Endpoint to get top 10 users from current month's leaderboard.
app.get('/leaderboard-current-month', async (req, res) => {
	const key = keyForCurrMonth(MONTHLY_LEADERBOARD_PREFIX)
	// ZREVRANGE returns members ordered from highest to lowest score.
	// Using the WITHSCORES option to include the scores in result.
	const leaderboard = await dragonfly.zrevrange(key, 0, 9, 'WITHSCORES')

	// Convert flat array of [member,score,member,score,...] to array of objects.
	const rankings = []
	for (let i = 0; i < leaderboard.length; i += 2) {
		rankings.push({
			userId: leaderboard[i],
			score: parseInt(leaderboard[i + 1]),
		})
	}

	res.json({ rankings })
})

// Start the server.
const PORT = 3000
app.listen(PORT, () => {
	console.log(`Server is running on http://localhost:${PORT}`)
})
